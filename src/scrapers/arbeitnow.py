import time
from typing import List, Optional
from datetime import datetime
import html2text
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class ArbeitnowScraper(BaseScraper):
    """Scraper for Arbeitnow API."""
    
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"
    
    @property
    def platform_name(self) -> str:
        return "arbeitnow"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from Arbeitnow API."""
        if not self.is_enabled():
            logger.info("Arbeitnow scraper is disabled")
            return []
        
        logger.info("🇩🇪 Starting Arbeitnow scraper...")
        
        an_config = self.config.get('scraping', {}).get('arbeitnow', {})
        max_pages = an_config.get('max_pages', 5)
        
        all_jobs = []
        seen_hashes = set()
        
        for page in range(1, max_pages + 1):
            try:
                jobs = self._fetch_page(page)
                
                if not jobs:
                    break  # No more results
                
                for job in jobs:
                    if job.job_hash not in seen_hashes:
                        seen_hashes.add(job.job_hash)
                        all_jobs.append(job)
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                error_msg = f"Error fetching page {page}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                break
        
        logger.info(f"   ✅ Arbeitnow: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_page(self, page: int) -> List[Job]:
        """Fetch a single page of jobs."""
        response = resilient_request(
            self.BASE_URL,
            params={"page": page},
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        data = response.json()
        jobs = []
        for item in data.get('data', []):
            job = self._parse_job(item)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item from the API response."""
        try:
            # Convert HTML description to plain text
            description = None
            if item.get('description'):
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                description = h.handle(item['description'])[:2000]  # Limit length
            
            # Parse location
            location = item.get('location', 'Germany')
            if item.get('remote'):
                location = f"{location} (Remote)"
            
            # Parse date
            posted_date = None
            if item.get('created_at'):
                try:
                    posted_date = datetime.fromtimestamp(item['created_at']).strftime('%Y-%m-%d')
                except:
                    pass
            
            return Job(
                title=item.get('title', 'Unknown Title'),
                company=item.get('company_name', 'Unknown Company'),
                location=location,
                url=item.get('url', ''),
                platform='arbeitnow',
                description=description,
                tags=item.get('tags', []),
                posted_date=posted_date
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse job item: {e}")
            return None


if __name__ == "__main__":
    # Test the scraper
    import yaml
    
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    scraper = ArbeitnowScraper(config)
    jobs = scraper.scrape()
    
    print(f"\nFound {len(jobs)} jobs")
    for job in jobs[:5]:
        print(f"  - {job.title} @ {job.company}")
