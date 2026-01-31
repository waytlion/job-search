import pytest
import yaml

from src.scrapers.base import Job
from src.scorer import JobScorer


@pytest.fixture
def config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def scorer(config):
    return JobScorer(config)


class TestMoneyScore:
    
    def test_high_salary_high_score(self, scorer):
        job = Job(
            title="Data Engineer",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test",
            salary_min=90000,
            salary_currency="EUR"
        )
        score = scorer._calculate_money_score(job)
        assert score >= 8
    
    def test_senior_title_bonus(self, scorer):
        job_senior = Job(
            title="Senior Data Scientist",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test"
        )
        job_junior = Job(
            title="Data Scientist",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test"
        )
        
        score_senior = scorer._calculate_money_score(job_senior)
        score_junior = scorer._calculate_money_score(job_junior)
        
        assert score_senior > score_junior
    
    def test_currency_conversion(self, scorer):
        job = Job(
            title="Data Engineer",
            company="Tech Corp",
            location="Remote",
            url="https://example.com",
            platform="test",
            salary_min=100000,  # USD
            salary_currency="USD"
        )
        
        # $100k USD ≈ €92k EUR (excellent)
        score = scorer._calculate_money_score(job)
        assert score >= 8


class TestPassionScore:
    
    def test_energy_keywords_boost(self, scorer):
        job = Job(
            title="Data Scientist - Energy Grid Optimization",
            company="Energy Corp",
            location="Munich",
            url="https://example.com",
            platform="test",
            description="Work on renewable energy and smart grid solutions"
        )
        score = scorer._calculate_passion_score(job)
        assert score >= 7
    
    def test_ml_keywords_boost(self, scorer):
        job = Job(
            title="Machine Learning Engineer",
            company="AI Startup",
            location="Berlin",
            url="https://example.com",
            platform="test",
            description="Deep learning, neural networks, transformer models"
        )
        score = scorer._calculate_passion_score(job)
        assert score >= 6
    
    def test_title_only_multiplier(self, scorer):
        """When no description, title keywords should be weighted more."""
        job_with_desc = Job(
            title="ML Engineer",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test",
            description="Build machine learning systems"
        )
        job_no_desc = Job(
            title="ML Engineer",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test",
            description=None
        )
        
        # Both should still get decent scores
        score_with = scorer._calculate_passion_score(job_with_desc)
        score_without = scorer._calculate_passion_score(job_no_desc)
        
        assert score_without >= 3  # Title-only should still score


class TestLocationScore:
    
    def test_bavaria_highest(self, scorer):
        job = Job(
            title="Data Scientist",
            company="BMW",
            location="Munich, Bavaria",
            url="https://example.com",
            platform="test"
        )
        score = scorer._calculate_location_score(job)
        assert score == 10
    
    def test_berlin_preferred(self, scorer):
        job = Job(
            title="Data Scientist",
            company="Startup",
            location="Berlin, Germany",
            url="https://example.com",
            platform="test"
        )
        score = scorer._calculate_location_score(job)
        assert score == 8
    
    def test_remote_decent(self, scorer):
        job = Job(
            title="Data Scientist",
            company="Remote Corp",
            location="Remote - Worldwide",
            url="https://example.com",
            platform="test"
        )
        score = scorer._calculate_location_score(job)
        assert score == 7
    
    def test_unknown_location(self, scorer):
        job = Job(
            title="Data Scientist",
            company="Unknown Corp",
            location="Somewhere else",
            url="https://example.com",
            platform="test"
        )
        score = scorer._calculate_location_score(job)
        assert score <= 3


class TestTotalScore:
    
    def test_perfect_job_high_score(self, scorer):
        """A job with all positive attributes should score very high."""
        job = Job(
            title="Senior Data Scientist - Energy Grid",
            company="Siemens Energy",
            location="Munich, Bavaria",
            url="https://example.com",
            platform="test",
            description="Machine learning for renewable energy optimization",
            salary_min=85000,
            salary_currency="EUR"
        )
        
        jobs = scorer.score_jobs([job])
        assert jobs[0].total_score >= 8
    
    def test_experience_penalty_applied(self, scorer):
        """Jobs requiring more experience should get penalty."""
        job = Job(
            title="Data Scientist",
            company="Tech Corp",
            location="Berlin",
            url="https://example.com",
            platform="test",
            description="Requires 7 years of experience",
            years_experience_required=7
        )
        
        jobs = scorer.score_jobs([job])
        # Money score should be reduced
        assert jobs[0].money_score < 5
