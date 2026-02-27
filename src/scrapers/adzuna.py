import os
import time
from typing import List, Optional
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class AdzunaScraper(BaseScraper):
    """
    Scraper for Adzuna API.
    
    Requires a free API key from https://developer.adzuna.com/
    Set ADZUNA_APP_ID and ADZUNA_APP_KEY in your .env file.
    If no key is provided, this scraper is silently skipped.
    """
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
    
    @property
    def platform_name(self) -> str:
        return "adzuna"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from Adzuna API."""
        if not self.is_enabled():
            logger.info("Adzuna scraper is disabled")
            return []
        
        app_id = os.environ.get('ADZUNA_APP_ID', '')
        app_key = os.environ.get('ADZUNA_APP_KEY', '')
        
        if not app_id or not app_key:
            logger.info("🔑 Adzuna: No API key configured — skipping. "
                       "Register free at https://developer.adzuna.com/")
            return []
        
        logger.info("🔍 Starting Adzuna scraper...")
        
        az_config = self.config.get('scraping', {}).get('adzuna', {})
        countries = az_config.get('countries', ['de', 'gb'])
        search_terms = az_config.get('search_terms', ['data scientist', 'machine learning'])
        max_pages = az_config.get('max_pages', 2)
        results_per_page = az_config.get('results_per_page', 50)
        
        all_jobs = []
        seen_hashes = set()
        
        for country in countries:
            for term in search_terms:
                for page in range(1, max_pages + 1):
                    try:
                        jobs = self._fetch_page(app_id, app_key, country, term, page, results_per_page)
                        if not jobs:
                            break
                        
                        for job in jobs:
                            if job.job_hash not in seen_hashes:
                                seen_hashes.add(job.job_hash)
                                all_jobs.append(job)
                        
                        time.sleep(0.5)
                    except Exception as e:
                        error_msg = f"Adzuna error ({country}/{term} p{page}): {str(e)}"
                        logger.error(error_msg)
                        self.errors.append(error_msg)
                        break
        
        logger.info(f"   ✅ Adzuna: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_page(self, app_id, app_key, country, term, page, results_per_page) -> List[Job]:
        """Fetch a page of results."""
        url = self.BASE_URL.format(country=country, page=page)
        
        response = resilient_request(
            url,
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": term,
                "results_per_page": results_per_page,
                "content-type": "application/json",
            },
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        data = response.json()
        jobs = []
        for item in data.get('results', []):
            job = self._parse_job(item, country)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: dict, country: str) -> Optional[Job]:
        """Parse a single Adzuna job."""
        try:
            # Location
            location_obj = item.get('location', {})
            display_name = location_obj.get('display_name', country.upper())
            
            # Salary
            salary_min = None
            salary_max = None
            salary_currency = 'EUR' if country == 'de' else 'GBP' if country == 'gb' else 'USD'
            salary_text = None
            
            if item.get('salary_min'):
                try:
                    salary_min = int(item['salary_min'])
                except (ValueError, TypeError):
                    pass
            if item.get('salary_max'):
                try:
                    salary_max = int(item['salary_max'])
                except (ValueError, TypeError):
                    pass
            
            if salary_min and salary_max:
                salary_text = f"{salary_currency} {salary_min:,} - {salary_max:,}"
            elif salary_min:
                salary_text = f"{salary_currency} {salary_min:,}+"
            
            # Date
            posted_date = None
            created = item.get('created', '')
            if created:
                try:
                    posted_date = created[:10]
                except:
                    pass
            
            # Tags from category
            tags = []
            cat = item.get('category', {})
            if cat.get('label'):
                tags.append(cat['label'])
            
            return Job(
                title=item.get('title', 'Unknown Title'),
                company=item.get('company', {}).get('display_name', 'Unknown Company'),
                location=display_name,
                url=item.get('redirect_url', ''),
                platform='adzuna',
                description=item.get('description', '')[:2000] if item.get('description') else None,
                tags=tags,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                salary_text=salary_text,
                posted_date=posted_date,
            )
        except Exception as e:
            logger.debug(f"Failed to parse Adzuna item: {e}")
            return None
