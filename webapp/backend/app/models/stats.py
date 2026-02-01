"""Statistics-related Pydantic models"""
from pydantic import BaseModel
from typing import List, Dict, Optional


class LocationCount(BaseModel):
    name: str
    count: int


class CompanyCount(BaseModel):
    name: str
    count: int


class DateCount(BaseModel):
    date: str
    count: int


class ScoreRange(BaseModel):
    range: str
    count: int


class StatsResponse(BaseModel):
    """Response model for dashboard statistics"""
    totalJobs: int
    validJobs: int
    filteredJobs: int
    avgScore: float
    topScore: float
    
    jobsByStatus: Dict[str, int]
    jobsByPlatform: Dict[str, int]
    
    topLocations: List[LocationCount]
    topCompanies: List[CompanyCount]
    
    jobsByDate: List[DateCount]
    scoreDistribution: List[ScoreRange]
    
    newToday: int
    newThisWeek: int
