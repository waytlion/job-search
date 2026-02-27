import time
from typing import List, Optional
from datetime import datetime
import html2text
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class JobicyScraper(BaseScraper):
    """Scraper for Jobicy API — remote job listings, no API key needed."""
    
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"
    
    @property
    def platform_name(self) -> str:
        return "jobicy"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from Jobicy API."""
        if not self.is_enabled():
            logger.info("Jobicy scraper is disabled")
            return []
        
        logger.info("🌐 Starting Jobicy scraper...")
        
        jc_config = self.config.get('scraping', {}).get('jobicy', {})
        tags = jc_config.get('tags', ['data-science', 'machine-learning', 'python'])
        count = jc_config.get('results_per_tag', 50)
        
        all_jobs = []
        seen_hashes = set()
        
        for tag in tags:
            try:
                jobs = self._fetch_tag(tag, count)
                for job in jobs:
                    if job.job_hash not in seen_hashes:
                        seen_hashes.add(job.job_hash)
                        all_jobs.append(job)
                
                time.sleep(0.5)
            except Exception as e:
                error_msg = f"Error fetching tag '{tag}': {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        logger.info(f"   ✅ Jobicy: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_tag(self, tag: str, count: int) -> List[Job]:
        """Fetch jobs for a specific tag."""
        response = resilient_request(
            self.BASE_URL,
            params={"count": count, "tag": tag},
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        data = response.json()
        jobs = []
        for item in data.get('jobs', []):
            job = self._parse_job(item)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job(self, item: dict) -> Optional[Job]:
        """Parse a single job item."""
        try:
            # Parse description
            description = None
            raw = item.get('jobDescription', '')
            if raw:
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                description = h.handle(raw)[:2000]
            
            # Parse location
            geo = item.get('jobGeo', 'Remote')
            location = geo if geo else 'Remote'
            
            # Parse salary
            salary_min = None
            salary_max = None
            salary_currency = None
            salary_text = None
            
            ann_salary_min = item.get('annualSalaryMin')
            ann_salary_max = item.get('annualSalaryMax')
            currency = item.get('salaryCurrency', 'USD')
            
            if ann_salary_min:
                try:
                    salary_min = int(ann_salary_min)
                    salary_currency = currency
                except (ValueError, TypeError):
                    pass
            if ann_salary_max:
                try:
                    salary_max = int(ann_salary_max)
                except (ValueError, TypeError):
                    pass
            
            if salary_min and salary_max:
                salary_text = f"{salary_currency} {salary_min:,} - {salary_max:,}"
            elif salary_min:
                salary_text = f"{salary_currency} {salary_min:,}+"
            
            # Parse date
            posted_date = None
            pub_date = item.get('pubDate', '')
            if pub_date:
                try:
                    posted_date = pub_date[:10]
                except:
                    pass
            
            # Tags
            tags = []
            if item.get('jobIndustry'):
                if isinstance(item['jobIndustry'], list):
                    tags = item['jobIndustry']
                else:
                    tags = [item['jobIndustry']]
            
            return Job(
                title=item.get('jobTitle', 'Unknown Title'),
                company=item.get('companyName', 'Unknown Company'),
                location=location,
                url=item.get('url', ''),
                platform='jobicy',
                description=description,
                tags=tags,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,
                salary_text=salary_text,
                posted_date=posted_date,
            )
        except Exception as e:
            logger.debug(f"Failed to parse Jobicy item: {e}")
            return None
