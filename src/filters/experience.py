import re
from typing import List, Optional
from src.scrapers.base import Job
from src.utils.logger import get_logger

logger = get_logger()


class ExperienceFilter:
    """Parse and filter based on experience requirements."""
    
    # Patterns to match experience requirements
    EXPERIENCE_PATTERNS = [
        r'(\d+)\+?\s*(?:years?|jahre?)\s*(?:of\s*)?(?:experience|erfahrung|berufserfahrung)',
        r'(?:experience|erfahrung|berufserfahrung)\s*(?:of\s*)?(\d+)\+?\s*(?:years?|jahre?)',
        r'(\d+)\s*-\s*\d+\s*(?:years?|jahre?)',
        r'(?:minimum|mindestens|min\.?)\s*(\d+)\s*(?:years?|jahre?)',
        r'(\d+)\+\s*(?:years?|jahre?)',
        r'(?:at least|wenigstens)\s*(\d+)\s*(?:years?|jahre?)',
    ]
    
    def __init__(self, config: dict):
        self.config = config
        filter_config = config.get('filtering', {})
        self.hard_filter_years = filter_config.get('hard_filter_experience_years', 10)
        self.penalty_threshold = filter_config.get('experience_penalty_threshold', 5)
        self.penalty_points = filter_config.get('experience_penalty_points', 2)
    
    def filter(self, jobs: List[Job]) -> List[Job]:
        """Parse experience requirements and apply filtering/penalties."""
        logger.info(f"📊 Running experience filter on {len(jobs)} jobs...")
        
        hard_filtered = 0
        penalized = 0
        
        for job in jobs:
            if job.filtered_out:
                continue
            
            # Parse experience from title and description
            text = (job.title + " " + (job.description or "")).lower()
            years_required = self._parse_experience(text)
            job.years_experience_required = years_required
            
            if years_required:
                # Hard filter for extreme requirements
                if years_required >= self.hard_filter_years:
                    job.filtered_out = True
                    job.filter_reason = f"Requires {years_required}+ years experience"
                    hard_filtered += 1
                # Penalty for above threshold
                elif years_required > self.penalty_threshold:
                    # Penalty will be applied during scoring
                    penalized += 1
        
        remaining = len([j for j in jobs if not j.filtered_out])
        logger.info(f"   ✅ Hard filtered {hard_filtered} jobs (10+ years), {penalized} will be penalized")
        logger.info(f"   ✅ {remaining} jobs remaining")
        
        return jobs
    
    def _parse_experience(self, text: str) -> Optional[int]:
        """Extract years of experience required from text."""
        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def get_penalty(self, job: Job) -> float:
        """Get experience penalty for a job."""
        if job.years_experience_required and job.years_experience_required > self.penalty_threshold:
            return self.penalty_points
        return 0
