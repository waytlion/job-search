import pytest
import yaml
from unittest.mock import patch, MagicMock

from src.scrapers import BundesagenturScraper, ArbeitnowScraper, RemoteOKScraper
from src.scrapers.base import Job


@pytest.fixture
def config():
    """Load test configuration."""
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


class TestBundesagenturScraper:
    
    def test_platform_name(self, config):
        scraper = BundesagenturScraper(config)
        assert scraper.platform_name == "bundesagentur"
    
    @patch('src.scrapers.bundesagentur.resilient_request')
    def test_parse_job(self, mock_request, config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'stellenangebote': [{
                'titel': 'Data Scientist',
                'arbeitgeber': 'Test Company',
                'arbeitsort': {'ort': 'Berlin', 'plz': '10115'},
                'hashId': 'abc123',
                'modifikationsTimestamp': '2024-01-30T10:00:00Z'
            }]
        }
        mock_request.return_value = mock_response
        
        scraper = BundesagenturScraper(config)
        jobs = scraper._fetch_jobs("Data Scientist", "Berlin", 50, 100)
        
        assert len(jobs) == 1
        assert jobs[0].title == 'Data Scientist'
        assert jobs[0].company == 'Test Company'
        assert 'Berlin' in jobs[0].location
        assert '?id=abc123' in jobs[0].url
    
    def test_parse_job_rejects_missing_hash(self, config):
        """Jobs without hashId or refnr must be rejected to prevent broken URLs."""
        scraper = BundesagenturScraper(config)
        
        item_no_ids = {
            'titel': 'Some Job',
            'arbeitgeber': 'Some Company',
            'arbeitsort': {'ort': 'Berlin'},
            # No hashId, no refnr
        }
        
        result = scraper._parse_job(item_no_ids)
        assert result is None, "Jobs without hashId/refnr should be rejected"
    
    def test_parse_job_rejects_empty_hash(self, config):
        """Jobs with empty hashId and empty refnr must be rejected."""
        scraper = BundesagenturScraper(config)
        
        item_empty = {
            'titel': 'Some Job',
            'arbeitgeber': 'Some Company',
            'arbeitsort': {'ort': 'Berlin'},
            'hashId': '',
            'refnr': '',
        }
        
        result = scraper._parse_job(item_empty)
        assert result is None, "Jobs with empty hashId/refnr should be rejected"


class TestArbeitnowScraper:
    
    def test_platform_name(self, config):
        scraper = ArbeitnowScraper(config)
        assert scraper.platform_name == "arbeitnow"
    
    @patch('src.scrapers.arbeitnow.resilient_request')
    def test_parse_job(self, mock_request, config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{
                'title': 'ML Engineer',
                'company_name': 'Startup GmbH',
                'location': 'Berlin',
                'url': 'https://example.com/job',
                'description': '<p>Great job!</p>',
                'tags': ['python', 'ml'],
                'remote': True,
                'created_at': 1706601600
            }]
        }
        mock_request.return_value = mock_response
        
        scraper = ArbeitnowScraper(config)
        jobs = scraper._fetch_page(1)
        
        assert len(jobs) == 1
        assert jobs[0].title == 'ML Engineer'
        assert 'Remote' in jobs[0].location


class TestRemoteOKScraper:
    
    def test_platform_name(self, config):
        scraper = RemoteOKScraper(config)
        assert scraper.platform_name == "remoteok"
    
    @patch('src.scrapers.remoteok.resilient_request')
    def test_parse_job(self, mock_request, config):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'legal': 'Legal text'},  # First item is always legal
            {
                'position': 'Remote Data Engineer',
                'company': 'Tech Inc',
                'location': 'Worldwide',
                'url': 'https://remoteok.com/job/123',
                'description': '<p>Amazing opportunity!</p>',
                'salary_min': 100000,
                'salary_max': 150000,
                'salary_currency': 'USD',
                'tags': ['python', 'data'],
                'date': '2024-01-30'
            }
        ]
        mock_request.return_value = mock_response
        
        scraper = RemoteOKScraper(config)
        jobs = scraper._fetch_tag('data')
        
        assert len(jobs) == 1
        assert jobs[0].title == 'Remote Data Engineer'
        assert jobs[0].salary_min == 100000


class TestJobHash:
    
    def test_job_hash_uniqueness(self):
        job1 = Job(
            title="Data Scientist",
            company="Company A",
            location="Berlin",
            url="https://example.com/1",
            platform="test"
        )
        job2 = Job(
            title="Data Scientist",
            company="Company A",
            location="Berlin",
            url="https://example.com/2",  # Different URL
            platform="test"
        )
        job3 = Job(
            title="ML Engineer",  # Different title
            company="Company A",
            location="Berlin",
            url="https://example.com/3",
            platform="test"
        )
        
        # Same title, company, location = same hash
        assert job1.job_hash == job2.job_hash
        
        # Different title = different hash
        assert job1.job_hash != job3.job_hash


class TestSafeScrape:
    """Test that safe_scrape never crashes the pipeline."""
    
    def test_safe_scrape_catches_exceptions(self, config):
        """safe_scrape should catch any exception and return empty list."""
        scraper = ArbeitnowScraper(config)
        
        # Force an exception inside scrape()
        with patch.object(scraper, 'scrape', side_effect=RuntimeError("API exploded")):
            result = scraper.safe_scrape()
        
        assert result == []
        assert len(scraper.errors) > 0
        assert "crashed" in scraper.errors[0].lower()
    
    def test_safe_scrape_respects_disabled(self, config):
        """safe_scrape should skip disabled scrapers."""
        config['scraping']['arbeitnow']['enabled'] = False
        scraper = ArbeitnowScraper(config)
        
        result = scraper.safe_scrape()
        assert result == []


class TestResilientRequest:
    """Test the resilient_request helper."""
    
    @patch('src.scrapers.base.requests.request')
    def test_returns_none_on_403(self, mock_req):
        """403 (bot detection) should return None immediately."""
        from src.scrapers.base import resilient_request
        
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_req.return_value = mock_resp
        
        result = resilient_request("https://blocked.com", platform_name="test")
        assert result is None
        # Should NOT retry — only 1 call
        assert mock_req.call_count == 1
    
    @patch('src.scrapers.base.requests.request')
    def test_returns_response_on_200(self, mock_req):
        """200 should return the response."""
        from src.scrapers.base import resilient_request
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_req.return_value = mock_resp
        
        result = resilient_request("https://ok.com", platform_name="test")
        assert result is not None
        assert result.status_code == 200
