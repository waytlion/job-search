"""Job-related Pydantic models"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    NOT_VIEWED = "not_viewed"
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    ARCHIVED = "archived"


class JobBase(BaseModel):
    """Base job model with common fields"""
    id: int
    job_hash: str
    title: str
    company: str
    location: Optional[str] = None
    url: str
    platform: str
    
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    salary_text: Optional[str] = None
    
    posted_date: Optional[str] = None
    scraped_at: Optional[str] = None
    
    money_score: Optional[float] = 0
    passion_score: Optional[float] = 0
    location_score: Optional[float] = 0
    total_score: Optional[float] = 0
    
    years_experience_required: Optional[int] = None
    filtered_out: Optional[bool] = False
    filter_reason: Optional[str] = None
    
    user_status: Optional[str] = "not_viewed"
    user_notes: Optional[str] = None
    user_updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class JobListItem(BaseModel):
    """Lighter job model for list view (no description)"""
    id: int
    job_hash: str
    title: str
    company: str
    location: Optional[str] = None
    url: str
    platform: str
    
    salary_text: Optional[str] = None
    posted_date: Optional[str] = None
    
    money_score: Optional[float] = 0
    passion_score: Optional[float] = 0
    location_score: Optional[float] = 0
    total_score: Optional[float] = 0
    
    user_status: Optional[str] = "not_viewed"
    
    class Config:
        from_attributes = True


class JobDetail(JobBase):
    """Full job model with description"""
    description: Optional[str] = None
    requirements: Optional[str] = None
    tags: Optional[str] = None


class JobUpdate(BaseModel):
    """Model for updating job user fields"""
    user_status: Optional[UserStatus] = None
    user_notes: Optional[str] = None


class JobsResponse(BaseModel):
    """Response model for paginated jobs"""
    jobs: List[JobListItem]
    total: int
    page: int
    limit: int
    totalPages: int
