import pytest
import yaml

from src.scrapers.base import Job
from src.filters import RelevanceFilter, ExperienceFilter


@pytest.fixture
def config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_jobs():
    return [
        Job(
            title="Data Scientist",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com/1",
            platform="test",
            description="Great ML role"
        ),
        Job(
            title="Delivery Driver",
            company="Logistics Inc",
            location="Munich",
            url="https://example.com/2",
            platform="test",
            description="Drive our vans"
        ),
        Job(
            title="Senior ML Engineer",
            company="AI Startup",
            location="Berlin",
            url="https://example.com/3",
            platform="test",
            description="Requires 3+ years experience in machine learning"
        ),
        Job(
            title="Head of Data Science",
            company="Big Corp",
            location="Hamburg",
            url="https://example.com/4",
            platform="test",
            description="Lead our team"
        ),
        Job(
            title="Junior Analyst",
            company="Finance Co",
            location="Frankfurt",
            url="https://example.com/5",
            platform="test",
            description="Entry level, 10+ years experience required"
        )
    ]


class TestRelevanceFilter:
    
    def test_filters_driver_jobs(self, config, sample_jobs):
        filter = RelevanceFilter(config)
        filtered = filter.filter(sample_jobs)
        
        driver_job = next(j for j in filtered if "Driver" in j.title)
        assert driver_job.filtered_out == True
        assert "driver" in driver_job.filter_reason.lower()
    
    def test_filters_head_of_roles(self, config, sample_jobs):
        filter = RelevanceFilter(config)
        filtered = filter.filter(sample_jobs)
        
        head_job = next(j for j in filtered if "Head of" in j.title)
        assert head_job.filtered_out == True
    
    def test_keeps_data_scientist(self, config, sample_jobs):
        filter = RelevanceFilter(config)
        filtered = filter.filter(sample_jobs)
        
        ds_job = next(j for j in filtered if j.title == "Data Scientist")
        assert ds_job.filtered_out == False


class TestExperienceFilter:
    
    def test_parses_experience_requirement(self, config, sample_jobs):
        filter = ExperienceFilter(config)
        filtered = filter.filter(sample_jobs)
        
        ml_job = next(j for j in filtered if "ML Engineer" in j.title)
        assert ml_job.years_experience_required == 3
    
    def test_hard_filters_extreme_experience(self, config, sample_jobs):
        filter = ExperienceFilter(config)
        filtered = filter.filter(sample_jobs)
        
        junior_job = next(j for j in filtered if "Junior Analyst" in j.title)
        assert junior_job.filtered_out == True
        assert "10" in junior_job.filter_reason
    
    def test_experience_patterns(self, config):
        filter = ExperienceFilter(config)
        
        test_cases = [
            ("5+ years of experience required", 5),
            ("minimum 3 years experience", 3),
            ("7 Jahre Berufserfahrung", 7),
            ("at least 4 years of ML experience", 4),
            ("2-3 years in data science", 2),
            ("no experience needed", None),
        ]
        
        for text, expected in test_cases:
            result = filter._parse_experience(text.lower())
            assert result == expected, f"Failed for: {text}"
