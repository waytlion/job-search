import time
from typing import List, Optional
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class TheMuseScraper(BaseScraper):
    """Scraper for The Muse public API — tech company jobs, no API key needed."""
    
    BASE_URL = "https://www.themuse.com/api/public/jobs"
    
    @property
    def platform_name(self) -> str:
        return "themuse"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from The Muse API."""
        if not self.is_enabled():
            logger.info("The Muse scraper is disabled")
            return []
        
        logger.info("💼 Starting The Muse scraper...")
        
        tm_config = self.config.get('scraping', {}).get('themuse', {})
        categories = tm_config.get('categories', [
            'Data Science',
            'Data and Analytics',
            'Software Engineering',
        ])
        max_pages = tm_config.get('max_pages', 3)
        
        all_jobs = []
        seen_hashes = set()
        
        for category in categories:
            for page in range(max_pages):
                try:
                    jobs = self._fetch_page(category, page)
                    if not jobs:
                        break
                    
                    for job in jobs:
                        if job.job_hash not in seen_hashes:
                            seen_hashes.add(job.job_hash)
                            all_jobs.append(job)
                    
                    time.sleep(0.3)
                except Exception as e:
                    error_msg = f"Error fetching '{category}' page {page}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    break
        
        logger.info(f"   ✅ The Muse: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_page(self, category: str, page: int) -> List[Job]:
        """Fetch a single page of jobs for a category."""
        response = resilient_request(
            self.BASE_URL,
            params={"category": category, "page": page},
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        data = response.json()
        jobs = []
        for item in data.get('results', []):
            job = self._parse_job(item)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item."""
        try:
            # Company info
            company_obj = item.get('company', {})
            company_name = company_obj.get('name', 'Unknown Company')
            
            # Location
            locations = item.get('locations', [])
            if locations:
                location_names = [loc.get('name', '') for loc in locations if loc.get('name')]
                location = ', '.join(location_names[:3]) if location_names else 'Remote'
            else:
                location = 'Remote'
            
            # Description
            description = None
            contents = item.get('contents', '')
            if contents:
                # contents is HTML; strip tags simply
                import re
                description = re.sub(r'<[^>]+>', ' ', contents)
                description = ' '.join(description.split())[:2000]
            
            # Date
            posted_date = None
            pub = item.get('publication_date', '')
            if pub:
                try:
                    posted_date = pub[:10]
                except:
                    pass
            
            # Tags from categories
            tags = [cat.get('name', '') for cat in item.get('categories', []) if cat.get('name')]
            
            # Level info
            levels = item.get('levels', [])
            level_names = [lv.get('name', '') for lv in levels if lv.get('name')]
            
            # URL
            url = item.get('refs', {}).get('landing_page', '')
            if not url:
                url = f"https://www.themuse.com/jobs/{item.get('id', '')}"
            
            return Job(
                title=item.get('name', 'Unknown Title'),
                company=company_name,
                location=location,
                url=url,
                platform='themuse',
                description=description,
                tags=tags + level_names,
                posted_date=posted_date,
            )
        except Exception as e:
            logger.debug(f"Failed to parse The Muse item: {e}")
            return None
