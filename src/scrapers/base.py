from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import hashlib
import time
import requests
from src.utils.logger import get_logger

logger = get_logger()


# ---------------------------------------------------------------------------
# Resilience helpers
# ---------------------------------------------------------------------------

def resilient_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict = None,
    params: dict = None,
    json_body: dict = None,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    platform_name: str = "unknown",
) -> Optional[requests.Response]:
    """
    HTTP request with retry, exponential backoff, and smart error handling.

    Returns the Response on success, or None if all retries are exhausted or
    the server returns a non-retryable status (401, 403, 404, 451).
    Never raises — always returns None on failure so the pipeline continues.
    """
    NON_RETRYABLE = {401, 403, 404, 451}

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout,
                allow_redirects=True,
            )

            # Non-retryable client errors (bot detection, forbidden, gone)
            if response.status_code in NON_RETRYABLE:
                logger.warning(
                    f"[{platform_name}] HTTP {response.status_code} from {url} "
                    f"— non-retryable, skipping."
                )
                return None

            # Server errors → retry
            if response.status_code >= 500:
                logger.warning(
                    f"[{platform_name}] HTTP {response.status_code} (attempt {attempt}/{max_retries})"
                )
                if attempt < max_retries:
                    _sleep = backoff_base ** attempt
                    time.sleep(_sleep)
                    continue
                return None

            # Rate-limited → back off and retry
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", backoff_base ** attempt))
                logger.warning(
                    f"[{platform_name}] Rate-limited (429). Waiting {retry_after}s..."
                )
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            logger.warning(f"[{platform_name}] Timeout (attempt {attempt}/{max_retries})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"[{platform_name}] Connection error (attempt {attempt}/{max_retries})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[{platform_name}] Request error: {e} (attempt {attempt}/{max_retries})")

        if attempt < max_retries:
            time.sleep(backoff_base ** attempt)

    logger.error(f"[{platform_name}] All {max_retries} attempts failed for {url}")
    return None


# ---------------------------------------------------------------------------
# Job data model
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Base scraper
# ---------------------------------------------------------------------------

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

    def safe_scrape(self) -> List[Job]:
        """
        Wrapper that catches ALL exceptions so one broken scraper never
        crashes the pipeline.  Returns [] on failure.
        """
        if not self.is_enabled():
            logger.info(f"[{self.platform_name}] Scraper is disabled — skipping")
            return []

        try:
            return self.scrape()
        except Exception as e:
            error_msg = f"[{self.platform_name}] Scraper crashed: {e}"
            logger.error(error_msg, exc_info=True)
            self.errors.append(error_msg)
            return []
