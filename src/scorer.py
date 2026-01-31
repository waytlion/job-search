from typing import List
from src.scrapers.base import Job
from src.filters.experience import ExperienceFilter
from src.utils.logger import get_logger

logger = get_logger()


class JobScorer:
    """Score and rank jobs based on configured criteria."""
    
    def __init__(self, config: dict):
        self.config = config
        self.scoring_config = config.get('scoring', {})
        self.experience_filter = ExperienceFilter(config)
    
    def score_jobs(self, jobs: List[Job]) -> List[Job]:
        """Calculate scores for all jobs."""
        logger.info(f"📈 Scoring {len(jobs)} jobs...")
        
        for job in jobs:
            if job.filtered_out:
                continue
            
            # Calculate individual scores
            job.money_score = self._calculate_money_score(job)
            job.passion_score = self._calculate_passion_score(job)
            job.location_score = self._calculate_location_score(job)
            
            # Apply experience penalty
            penalty = self.experience_filter.get_penalty(job)
            if penalty > 0:
                job.money_score = max(0, job.money_score - penalty)
            
            # Calculate weighted total
            weights = self.scoring_config.get('weights', {})
            job.total_score = (
                weights.get('money', 0.33) * job.money_score +
                weights.get('passion', 0.34) * job.passion_score +
                weights.get('location', 0.33) * job.location_score
            )
        
        # Sort by total score (descending)
        jobs.sort(key=lambda x: x.total_score, reverse=True)
        
        logger.info(f"   ✅ Scoring complete. Top score: {jobs[0].total_score:.2f}" if jobs else "   ⚠️ No jobs to score")
        
        return jobs
    
    def _calculate_money_score(self, job: Job) -> float:
        """Calculate money score (0-10)."""
        score = 5.0  # Default neutral score
        money_config = self.scoring_config.get('money', {})
        
        # Salary scoring
        if job.salary_min:
            salary_eur = self._convert_to_eur(job.salary_min, job.salary_currency)
            thresholds = money_config.get('salary_thresholds', {})
            
            if salary_eur >= thresholds.get('excellent', 80000):
                score = 10.0
            elif salary_eur >= thresholds.get('great', 65000):
                score = 8.0
            elif salary_eur >= thresholds.get('good', 50000):
                score = 6.0
            elif salary_eur >= thresholds.get('average', 40000):
                score = 4.0
            else:
                score = 2.0
        
        # Seniority bonus
        title_lower = job.title.lower()
        seniority_keywords = money_config.get('seniority_keywords', {})
        
        if any(kw in title_lower for kw in seniority_keywords.get('high', [])):
            score = min(score + 3, 10.0)
        elif any(kw in title_lower for kw in seniority_keywords.get('medium', [])):
            score = min(score + 1.5, 10.0)
        
        return score
    
    def _calculate_passion_score(self, job: Job) -> float:
        """Calculate passion score (0-10)."""
        score = 0.0
        passion_config = self.scoring_config.get('passion', {})
        
        # Determine if we need to use title-only scoring
        has_description = bool(job.description and len(job.description.strip()) > 50)
        
        # Text to analyze
        title_text = job.title.lower()
        full_text = (job.title + " " + (job.description or "")).lower()
        
        # If no description, use title with multiplier
        multiplier = 1.0
        if not has_description:
            multiplier = passion_config.get('title_weight_multiplier', 2.0)
            text = title_text
        else:
            text = full_text
        
        # Energy keywords
        energy_keywords = passion_config.get('energy_keywords', [])
        energy_matches = sum(1 for kw in energy_keywords if kw.lower() in text)
        energy_points = passion_config.get('energy_points', 4)
        energy_max = passion_config.get('energy_max', 7)
        score += min(energy_matches * energy_points * multiplier, energy_max)
        
        # ML/AI keywords
        ml_keywords = passion_config.get('ml_keywords', [])
        ml_matches = sum(1 for kw in ml_keywords if kw.lower() in text)
        ml_points = passion_config.get('ml_points', 3)
        ml_max = passion_config.get('ml_max', 6)
        score += min(ml_matches * ml_points * multiplier, ml_max)
        
        # Tech keywords
        tech_keywords = passion_config.get('tech_keywords', [])
        tech_matches = sum(1 for kw in tech_keywords if kw.lower() in text)
        tech_points = passion_config.get('tech_points', 1)
        tech_max = passion_config.get('tech_max', 3)
        score += min(tech_matches * tech_points * multiplier, tech_max)
        
        return min(score, 10.0)
    
    def _calculate_location_score(self, job: Job) -> float:
        """Calculate location score (0-10)."""
        location_config = self.scoring_config.get('location', {})
        location = job.location.lower()
        
        # Check tiers in order of preference
        tiers = [
            ('tier1_bavaria', 10),
            ('tier2_preferred_germany', 8),
            ('tier4_remote', 7),  # Check remote before general germany
            ('tier3_germany', 6),
            ('tier5_europe', 4),
        ]
        
        for tier_name, default_score in tiers:
            tier_config = location_config.get(tier_name, {})
            tier_score = tier_config.get('score', default_score)
            keywords = tier_config.get('keywords', [])
            
            if any(kw.lower() in location for kw in keywords):
                return float(tier_score)
        
        return float(location_config.get('default_score', 2))
    
    def _convert_to_eur(self, amount: int, currency: str) -> int:
        """Convert salary to EUR."""
        if not currency or currency.upper() == 'EUR':
            return amount
        
        conversion = self.scoring_config.get('money', {}).get('currency_conversion', {})
        rate = conversion.get(currency.upper(), 1.0)
        return int(amount * rate)
