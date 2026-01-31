import re
from typing import List
from src.scrapers.base import Job
from src.utils.logger import get_logger

logger = get_logger()


class RelevanceFilter:
    """Filter out irrelevant jobs (drivers, retail, etc.)."""
    
    def __init__(self, config: dict):
        self.config = config
        filter_config = config.get('filtering', {})
        self.irrelevant_keywords = filter_config.get('irrelevant_keywords', [])
        self.hard_filter_keywords = filter_config.get('hard_filter_keywords', [])
    
    def filter(self, jobs: List[Job]) -> List[Job]:
        """Filter jobs and mark irrelevant ones."""
        logger.info(f"🔍 Running relevance filter on {len(jobs)} jobs...")
        
        filtered_count = 0
        
        for job in jobs:
            # Check title and description
            text_to_check = (job.title + " " + (job.description or "")).lower()
            
            # Check for irrelevant keywords
            for keyword in self.irrelevant_keywords:
                if keyword.lower() in text_to_check:
                    job.filtered_out = True
                    job.filter_reason = f"Irrelevant keyword: {keyword}"
                    filtered_count += 1
                    break
            
            # Check for hard filter (too senior roles)
            if not job.filtered_out:
                for keyword in self.hard_filter_keywords:
                    if keyword.lower() in job.title.lower():
                        job.filtered_out = True
                        job.filter_reason = f"Too senior role: {keyword}"
                        filtered_count += 1
                        break
        
        remaining = len([j for j in jobs if not j.filtered_out])
        logger.info(f"   ✅ Filtered out {filtered_count} irrelevant jobs, {remaining} remaining")
        
        return jobs
