from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import hashlib


@dataclass
class Job:
    """Standardized job data structure."""
    title: str
    company: str
    location: str
    url: str
    platform: str
    
    # Optional fields
    description: Optional[str] = None
    requirements: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Salary info
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    salary_text: Optional[str] = None
    
    # Metadata
    posted_date: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    # Scores (set later)
    money_score: float = 0.0
    passion_score: float = 0.0
    location_score: float = 0.0
    total_score: float = 0.0
    
    # Filtering
    years_experience_required: Optional[int] = None
    filtered_out: bool = False
    filter_reason: Optional[str] = None
    
    @property
    def job_hash(self) -> str:
        """Generate unique hash for deduplication."""
        unique_string = f"{self.title.lower().strip()}|{self.company.lower().strip()}|{self.location.lower().strip()}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            'job_hash': self.job_hash,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'platform': self.platform,
            'description': self.description,
            'requirements': self.requirements,
            'tags': ','.join(self.tags) if self.tags else None,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_currency': self.salary_currency,
            'salary_text': self.salary_text,
            'posted_date': self.posted_date,
            'scraped_at': self.scraped_at.isoformat(),
            'money_score': self.money_score,
            'passion_score': self.passion_score,
            'location_score': self.location_score,
            'total_score': self.total_score,
            'years_experience_required': self.years_experience_required,
            'filtered_out': self.filtered_out,
            'filter_reason': self.filter_reason
        }


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""
    
    def __init__(self, config: dict):
        self.config = config
        self.jobs: List[Job] = []
        self.errors: List[str] = []
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name."""
        pass
    
    @abstractmethod
    def scrape(self) -> List[Job]:
        """Scrape jobs from the platform. Returns list of Job objects."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this scraper is enabled in config."""
        scraper_config = self.config.get('scraping', {}).get(self.platform_name.lower(), {})
        return scraper_config.get('enabled', True)
