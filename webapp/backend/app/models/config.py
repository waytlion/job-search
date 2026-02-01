"""Configuration-related Pydantic models"""
from pydantic import BaseModel
from typing import List, Dict, Optional


class ScoringWeights(BaseModel):
    money: float = 0.33
    passion: float = 0.34
    location: float = 0.33


class ConfigResponse(BaseModel):
    """Response model for configuration"""
    scoring_weights: ScoringWeights
    money_thresholds: Dict[str, int]
    passion_keywords: Dict[str, List[str]]
    location_tiers: Dict[str, Dict]
    
    
class ConfigUpdate(BaseModel):
    """Model for updating configuration"""
    scoring_weights: Optional[ScoringWeights] = None


class SyncResponse(BaseModel):
    """Response model for sync operation"""
    success: bool
    newJobs: int
    lastSync: str
    errors: List[str] = []
