import requests
import time
from typing import List, Optional
from datetime import datetime
from .base import BaseScraper, Job
from src.utils.logger import get_logger

logger = get_logger()


class BundesagenturScraper(BaseScraper):
    """Scraper for Bundesagentur für Arbeit API."""
    
    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
    HEADERS = {
        "Accept": "application/json",
        "X-API-Key": "jobboerse-jobsuche"
    }
    
    @property
    def platform_name(self) -> str:
        return "bundesagentur"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from Bundesagentur API."""
        if not self.is_enabled():
            logger.info("Bundesagentur scraper is disabled")
            return []
        
        logger.info("🏛️  Starting Bundesagentur scraper...")
        
        ba_config = self.config.get('scraping', {}).get('bundesagentur', {})
        locations = ba_config.get('locations', ['Berlin'])
        search_terms = ba_config.get('search_terms', ['Data Scientist'])
        radius = ba_config.get('radius_km', 50)
        results_per_page = ba_config.get('results_per_page', 100)
        
        all_jobs = []
        seen_hashes = set()
        
        for location in locations:
            for term in search_terms:
                try:
                    jobs = self._fetch_jobs(term, location, radius, results_per_page)
                    
                    # Deduplicate within this scrape
                    for job in jobs:
                        if job.job_hash not in seen_hashes:
                            seen_hashes.add(job.job_hash)
                            all_jobs.append(job)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_msg = f"Error fetching '{term}' in {location}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
        
        logger.info(f"   ✅ Bundesagentur: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_jobs(self, search_term: str, location: str, radius: int, size: int) -> List[Job]:
        """Fetch jobs for a specific search term and location."""
        params = {
            "was": search_term,
            "wo": location,
            "umkreis": radius,
            "page": 1,
            "size": size,
            "angebotsart": 1  # Full-time only
        }
        
        jobs = []
        
        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.HEADERS,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('stellenangebote', []):
                job = self._parse_job(item)
                if job:
                    jobs.append(job)
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {search_term} in {location}: {e}")
            raise
        
        return jobs
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item from the API response."""
        try:
            # Extract location
            arbeitsort = item.get('arbeitsort', {})
            location = arbeitsort.get('ort', 'Germany')
            if arbeitsort.get('plz'):
                location = f"{arbeitsort.get('plz')} {location}"
            
            # Build job URL
            hash_id = item.get('hashId', '')
            url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{hash_id}"
            
            # Parse date
            posted_date = None
            if item.get('modifikationsTimestamp'):
                try:
                    posted_date = item['modifikationsTimestamp'][:10]
                except:
                    pass
            
            return Job(
                title=item.get('titel', 'Unknown Title'),
                company=item.get('arbeitgeber', 'Unknown Company'),
                location=location,
                url=url,
                platform='bundesagentur',
                description=None,  # Not available in list view
                posted_date=posted_date,
                tags=[]
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse job item: {e}")
            return None


if __name__ == "__main__":
    # Test the scraper
    import yaml
    
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    scraper = BundesagenturScraper(config)
    jobs = scraper.scrape()
    
    print(f"\nFound {len(jobs)} jobs")
    for job in jobs[:5]:
        print(f"  - {job.title} @ {job.company} ({job.location})")
