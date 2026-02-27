import time
from typing import List, Optional
from datetime import datetime
import html2text
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class BundesagenturScraper(BaseScraper):
    """Scraper for Bundesagentur für Arbeit API."""
    
    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
    DETAIL_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/{hash_id}"
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
        fetch_descriptions = ba_config.get('fetch_descriptions', True)
        
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
        
        # Fetch descriptions for top jobs (limit to avoid rate-limiting)
        if fetch_descriptions and all_jobs:
            max_desc = ba_config.get('max_description_fetches', 50)
            self._fetch_descriptions(all_jobs[:max_desc])
        
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
        
        response = resilient_request(
            self.BASE_URL,
            headers=self.HEADERS,
            params=params,
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        data = response.json()
        jobs = []
        for item in data.get('stellenangebote', []):
            job = self._parse_job(item)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item from the API response."""
        try:
            # Extract location
            arbeitsort = item.get('arbeitsort', {})
            location = arbeitsort.get('ort', 'Germany')
            if arbeitsort.get('plz'):
                location = f"{arbeitsort.get('plz')} {location}"
            
            # Build job URL — validate hashId and use refnr as fallback
            hash_id = item.get('hashId', '')
            refnr = item.get('refnr', '')
            
            if hash_id:
                url = f"https://www.arbeitsagentur.de/jobsuche/suche?id={hash_id}"
            elif refnr:
                url = f"https://www.arbeitsagentur.de/jobsuche/suche?was={refnr}"
            else:
                # Skip jobs with no linkable ID
                logger.debug("Skipping job without hashId or refnr")
                return None
            
            # Parse date
            posted_date = None
            if item.get('modifikationsTimestamp'):
                try:
                    posted_date = item['modifikationsTimestamp'][:10]
                except:
                    pass
            elif item.get('eintrittsdatum'):
                posted_date = item['eintrittsdatum'][:10]
            
            return Job(
                title=item.get('titel', 'Unknown Title'),
                company=item.get('arbeitgeber', 'Unknown Company'),
                location=location,
                url=url,
                platform='bundesagentur',
                description=None,  # Fetched separately if enabled
                posted_date=posted_date,
                tags=[]
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse job item: {e}")
            return None
    
    def _fetch_descriptions(self, jobs: List[Job]):
        """Fetch full descriptions from the detail API for better scoring."""
        logger.info(f"   📝 Fetching descriptions for {len(jobs)} Bundesagentur jobs...")
        
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        
        fetched = 0
        for job in jobs:
            # Extract hashId from URL
            hash_id = ""
            if "id=" in job.url:
                hash_id = job.url.split("id=")[-1].split("&")[0]
            
            if not hash_id:
                continue
            
            detail_url = self.DETAIL_URL.format(hash_id=hash_id)
            response = resilient_request(
                detail_url,
                headers=self.HEADERS,
                timeout=15,
                max_retries=2,
                platform_name=self.platform_name,
            )
            
            if response is not None:
                try:
                    detail = response.json()
                    raw_desc = detail.get('stellenbeschreibung', '')
                    if raw_desc:
                        job.description = h.handle(raw_desc)[:2000]
                        fetched += 1
                except Exception:
                    pass
            
            # Be gentle with rate limiting
            time.sleep(0.3)
        
        logger.info(f"   ✅ Fetched {fetched}/{len(jobs)} descriptions")


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
        print(f"    URL: {job.url}")
        print(f"    Desc: {(job.description or 'None')[:80]}...")
