"""Statistics API routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models.stats import StatsResponse, LocationCount, CompanyCount, DateCount, ScoreRange

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Total jobs
    result = db.execute(text("SELECT COUNT(*) FROM jobs"))
    total_jobs = result.scalar()
    
    # Valid jobs (not filtered)
    result = db.execute(text("SELECT COUNT(*) FROM jobs WHERE filtered_out = 0 OR filtered_out IS NULL"))
    valid_jobs = result.scalar()
    
    # Filtered jobs
    filtered_jobs = total_jobs - valid_jobs
    
    # Average and top score
    result = db.execute(text("""
        SELECT AVG(total_score), MAX(total_score) 
        FROM jobs 
        WHERE (filtered_out = 0 OR filtered_out IS NULL)
    """))
    row = result.fetchone()
    avg_score = round(row[0] or 0, 2)
    top_score = round(row[1] or 0, 2)
    
    # Jobs by status
    result = db.execute(text("""
        SELECT COALESCE(user_status, 'not_viewed'), COUNT(*) 
        FROM jobs 
        WHERE (filtered_out = 0 OR filtered_out IS NULL)
        GROUP BY user_status
    """))
    jobs_by_status = {row[0]: row[1] for row in result.fetchall()}
    
    # Jobs by platform
    result = db.execute(text("""
        SELECT platform, COUNT(*) 
        FROM jobs 
        GROUP BY platform
    """))
    jobs_by_platform = {row[0]: row[1] for row in result.fetchall()}
    
    # Top locations (extract city name)
    result = db.execute(text("""
        SELECT location, COUNT(*) as cnt 
        FROM jobs 
        WHERE (filtered_out = 0 OR filtered_out IS NULL) AND location IS NOT NULL
        GROUP BY location 
        ORDER BY cnt DESC 
        LIMIT 10
    """))
    top_locations = [LocationCount(name=row[0], count=row[1]) for row in result.fetchall()]
    
    # Top companies
    result = db.execute(text("""
        SELECT company, COUNT(*) as cnt 
        FROM jobs 
        WHERE (filtered_out = 0 OR filtered_out IS NULL)
        GROUP BY company 
        ORDER BY cnt DESC 
        LIMIT 10
    """))
    top_companies = [CompanyCount(name=row[0], count=row[1]) for row in result.fetchall()]
    
    # Jobs by date (last 30 days)
    result = db.execute(text("""
        SELECT DATE(scraped_at) as date, COUNT(*) as cnt 
        FROM jobs 
        WHERE scraped_at >= DATE('now', '-30 days')
        GROUP BY DATE(scraped_at) 
        ORDER BY date
    """))
    jobs_by_date = [DateCount(date=row[0], count=row[1]) for row in result.fetchall()]
    
    # Score distribution
    score_ranges = [
        ("9-10", 9, 10),
        ("8-9", 8, 9),
        ("7-8", 7, 8),
        ("6-7", 6, 7),
        ("5-6", 5, 6),
        ("0-5", 0, 5),
    ]
    score_distribution = []
    for range_name, min_score, max_score in score_ranges:
        if max_score == 10:
            result = db.execute(text("""
                SELECT COUNT(*) FROM jobs 
                WHERE (filtered_out = 0 OR filtered_out IS NULL)
                AND total_score >= :min AND total_score <= :max
            """), {"min": min_score, "max": max_score})
        else:
            result = db.execute(text("""
                SELECT COUNT(*) FROM jobs 
                WHERE (filtered_out = 0 OR filtered_out IS NULL)
                AND total_score >= :min AND total_score < :max
            """), {"min": min_score, "max": max_score})
        count = result.scalar()
        score_distribution.append(ScoreRange(range=range_name, count=count))
    
    # New today
    today = datetime.now().strftime("%Y-%m-%d")
    result = db.execute(text("""
        SELECT COUNT(*) FROM jobs 
        WHERE DATE(scraped_at) = :today
    """), {"today": today})
    new_today = result.scalar()
    
    # New this week
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    result = db.execute(text("""
        SELECT COUNT(*) FROM jobs 
        WHERE DATE(scraped_at) >= :week_ago
    """), {"week_ago": week_ago})
    new_this_week = result.scalar()
    
    return StatsResponse(
        totalJobs=total_jobs,
        validJobs=valid_jobs,
        filteredJobs=filtered_jobs,
        avgScore=avg_score,
        topScore=top_score,
        jobsByStatus=jobs_by_status,
        jobsByPlatform=jobs_by_platform,
        topLocations=top_locations,
        topCompanies=top_companies,
        jobsByDate=jobs_by_date,
        scoreDistribution=score_distribution,
        newToday=new_today,
        newThisWeek=new_this_week
    )
