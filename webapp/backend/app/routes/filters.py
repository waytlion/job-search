"""Filter options API routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.connection import get_db

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("/options")
async def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options (for populating dropdowns)"""
    
    # Get unique locations
    result = db.execute(text("""
        SELECT DISTINCT location 
        FROM jobs 
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
        LIMIT 100
    """))
    locations = [row[0] for row in result.fetchall()]
    
    # Get unique companies
    result = db.execute(text("""
        SELECT DISTINCT company 
        FROM jobs 
        WHERE company IS NOT NULL AND company != ''
        ORDER BY company
        LIMIT 200
    """))
    companies = [row[0] for row in result.fetchall()]
    
    # Get unique platforms
    result = db.execute(text("""
        SELECT DISTINCT platform 
        FROM jobs 
        WHERE platform IS NOT NULL
        ORDER BY platform
    """))
    platforms = [row[0] for row in result.fetchall()]
    
    # Get status options
    statuses = [
        "not_viewed",
        "not_applied", 
        "interested",
        "applied",
        "not_interested",
        "archived"
    ]
    
    return {
        "locations": locations,
        "companies": companies,
        "platforms": platforms,
        "statuses": statuses
    }
