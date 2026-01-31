import requests
import time
from typing import List, Optional
from datetime import datetime
import html2text
from .base import BaseScraper, Job
from src.utils.logger import get_logger

logger = get_logger()


class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK API."""
    
    BASE_URL = "https://remoteok.com/api"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    @property
    def platform_name(self) -> str:
        return "remoteok"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from RemoteOK API."""
        if not self.is_enabled():
            logger.info("RemoteOK scraper is disabled")
            return []
        
        logger.info("🌍 Starting RemoteOK scraper...")
        
        ro_config = self.config.get('scraping', {}).get('remoteok', {})
        tags = ro_config.get('tags', ['data'])
        
        all_jobs = []
        seen_hashes = set()
        
        for tag in tags:
            try:
                jobs = self._fetch_tag(tag)
                
                for job in jobs:
                    if job.job_hash not in seen_hashes:
                        seen_hashes.add(job.job_hash)
                        all_jobs.append(job)
                
                # Rate limiting - RemoteOK is sensitive
                time.sleep(1.0)
                
            except Exception as e:
                error_msg = f"Error fetching tag '{tag}': {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        logger.info(f"   ✅ RemoteOK: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_tag(self, tag: str) -> List[Job]:
        """Fetch jobs for a specific tag."""
        url = f"{self.BASE_URL}?tag={tag}"
        
        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            # Skip index 0 (legal text)
            for item in data[1:]:
                job = self._parse_job(item)
                if job:
                    jobs.append(job)
            
            return jobs
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for tag {tag}: {e}")
            raise
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item from the API response."""
        try:
            # Convert HTML description to plain text
            description = None
            if item.get('description'):
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                description = h.handle(item['description'])[:2000]
            
            # Parse location
            location = item.get('location', 'Remote')
            if not location or location.strip() == '':
                location = '🌍 Worldwide Remote'
            
            # Parse salary
            salary_min = item.get('salary_min')
            salary_max = item.get('salary_max')
            salary_currency = item.get('salary_currency', 'USD') if salary_min else None
            
            salary_text = None
            if salary_min and salary_max:
                salary_text = f"${salary_min:,} - ${salary_max:,} {salary_currency}"
            elif salary_min:
                salary_text = f"${salary_min:,}+ {salary_currency}"
            
            # Parse date
            posted_date = None
            if item.get('date'):
                try:
                    posted_date = item['date'][:10]
                except:
                    pass
            
            # Parse tags
            tags = item.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            
            return Job(
                title=item.get('position', 'Unknown Position'),
                company=item.get('company', 'Unknown Company'),
                location=location,
                url=item.get('url', ''),
                platform='remoteok',
                description=description,
                tags=tags,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                salary_text=salary_text,
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
    
    scraper = RemoteOKScraper(config)
    jobs = scraper.scrape()
    
    print(f"\nFound {len(jobs)} jobs")
    for job in jobs[:5]:
        print(f"  - {job.title} @ {job.company} - {job.salary_text or 'No salary'}")
