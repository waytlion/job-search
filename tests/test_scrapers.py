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
    
    @patch('src.scrapers.bundesagentur.requests.get')
    def test_parse_job(self, mock_get, config):
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
        mock_get.return_value = mock_response
        
        scraper = BundesagenturScraper(config)
        jobs = scraper._fetch_jobs("Data Scientist", "Berlin", 50, 100)
        
        assert len(jobs) == 1
        assert jobs[0].title == 'Data Scientist'
        assert jobs[0].company == 'Test Company'
        assert 'Berlin' in jobs[0].location


class TestArbeitnowScraper:
    
    def test_platform_name(self, config):
        scraper = ArbeitnowScraper(config)
        assert scraper.platform_name == "arbeitnow"
    
    @patch('src.scrapers.arbeitnow.requests.get')
    def test_parse_job(self, mock_get, config):
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
        mock_get.return_value = mock_response
        
        scraper = ArbeitnowScraper(config)
        jobs = scraper._fetch_page(1)
        
        assert len(jobs) == 1
        assert jobs[0].title == 'ML Engineer'
        assert 'Remote' in jobs[0].location


class TestRemoteOKScraper:
    
    def test_platform_name(self, config):
        scraper = RemoteOKScraper(config)
        assert scraper.platform_name == "remoteok"
    
    @patch('src.scrapers.remoteok.requests.get')
    def test_parse_job(self, mock_get, config):
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
        mock_get.return_value = mock_response
        
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
