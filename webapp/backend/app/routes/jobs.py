"""Jobs API routes"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime

from app.database.connection import get_db
from app.models.job import JobListItem, JobDetail, JobUpdate, JobsResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobsResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("total_score"),
    order: str = Query("desc"),
    minScore: Optional[float] = Query(None, ge=0, le=10),
    maxScore: Optional[float] = Query(None, ge=0, le=10),
    locations: Optional[str] = Query(None),
    companies: Optional[str] = Query(None),
    platforms: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    dateFrom: Optional[str] = Query(None),
    dateTo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    hideFiltered: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get paginated, filtered jobs"""
    
    # Build WHERE clause
    conditions = []
    params = {}
    
    if hideFiltered:
        conditions.append("(filtered_out = 0 OR filtered_out IS NULL)")
    
    if minScore is not None:
        conditions.append("total_score >= :minScore")
        params["minScore"] = minScore
    
    if maxScore is not None:
        conditions.append("total_score <= :maxScore")
        params["maxScore"] = maxScore
    
    if locations:
        location_list = [loc.strip() for loc in locations.split(",")]
        location_conditions = " OR ".join([f"LOWER(location) LIKE :loc{i}" for i in range(len(location_list))])
        conditions.append(f"({location_conditions})")
        for i, loc in enumerate(location_list):
            params[f"loc{i}"] = f"%{loc.lower()}%"
    
    if companies:
        company_list = [c.strip() for c in companies.split(",")]
        company_conditions = " OR ".join([f"LOWER(company) LIKE :comp{i}" for i in range(len(company_list))])
        conditions.append(f"({company_conditions})")
        for i, comp in enumerate(company_list):
            params[f"comp{i}"] = f"%{comp.lower()}%"
    
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
        placeholders = ",".join([f":plat{i}" for i in range(len(platform_list))])
        conditions.append(f"platform IN ({placeholders})")
        for i, plat in enumerate(platform_list):
            params[f"plat{i}"] = plat
    
    if status and status != "all":
        conditions.append("user_status = :status")
        params["status"] = status
    
    if dateFrom:
        conditions.append("scraped_at >= :dateFrom")
        params["dateFrom"] = dateFrom
    
    if dateTo:
        conditions.append("scraped_at <= :dateTo")
        params["dateTo"] = dateTo
    
    if search:
        conditions.append("(LOWER(title) LIKE :search OR LOWER(company) LIKE :search OR LOWER(description) LIKE :search)")
        params["search"] = f"%{search.lower()}%"
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Validate sort column
    valid_sort_columns = ["total_score", "money_score", "passion_score", "location_score", 
                          "title", "company", "location", "scraped_at", "posted_date"]
    if sort not in valid_sort_columns:
        sort = "total_score"
    
    order_dir = "DESC" if order.lower() == "desc" else "ASC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_clause}"
    result = db.execute(text(count_query), params)
    total = result.scalar()
    
    # Get paginated results
    offset = (page - 1) * limit
    params["limit"] = limit
    params["offset"] = offset
    
    query = f"""
        SELECT id, job_hash, title, company, location, url, platform,
               salary_text, posted_date, money_score, passion_score,
               location_score, total_score, user_status
        FROM jobs 
        WHERE {where_clause}
        ORDER BY {sort} {order_dir}
        LIMIT :limit OFFSET :offset
    """
    
    result = db.execute(text(query), params)
    rows = result.fetchall()
    
    jobs = []
    for row in rows:
        jobs.append(JobListItem(
            id=row[0],
            job_hash=row[1],
            title=row[2],
            company=row[3],
            location=row[4],
            url=row[5],
            platform=row[6],
            salary_text=row[7],
            posted_date=row[8],
            money_score=row[9] or 0,
            passion_score=row[10] or 0,
            location_score=row[11] or 0,
            total_score=row[12] or 0,
            user_status=row[13] or "not_viewed"
        ))
    
    return JobsResponse(
        jobs=jobs,
        total=total,
        page=page,
        limit=limit,
        totalPages=(total + limit - 1) // limit if total > 0 else 1
    )


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get single job by ID"""
    query = """
        SELECT id, job_hash, title, company, location, url, platform,
               description, requirements, tags,
               salary_min, salary_max, salary_currency, salary_text,
               posted_date, scraped_at,
               money_score, passion_score, location_score, total_score,
               years_experience_required, filtered_out, filter_reason,
               user_status, user_notes, user_updated_at
        FROM jobs WHERE id = :job_id
    """
    
    result = db.execute(text(query), {"job_id": job_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobDetail(
        id=row[0],
        job_hash=row[1],
        title=row[2],
        company=row[3],
        location=row[4],
        url=row[5],
        platform=row[6],
        description=row[7],
        requirements=row[8],
        tags=row[9],
        salary_min=row[10],
        salary_max=row[11],
        salary_currency=row[12],
        salary_text=row[13],
        posted_date=row[14],
        scraped_at=row[15],
        money_score=row[16] or 0,
        passion_score=row[17] or 0,
        location_score=row[18] or 0,
        total_score=row[19] or 0,
        years_experience_required=row[20],
        filtered_out=bool(row[21]),
        filter_reason=row[22],
        user_status=row[23] or "not_viewed",
        user_notes=row[24],
        user_updated_at=row[25]
    )


@router.patch("/{job_id}", response_model=JobDetail)
async def update_job(
    job_id: int,
    update: JobUpdate,
    db: Session = Depends(get_db)
):
    """Update job user status/notes"""
    
    # Build UPDATE query
    updates = []
    params = {"job_id": job_id, "updated_at": datetime.now().isoformat()}
    
    if update.user_status is not None:
        updates.append("user_status = :user_status")
        params["user_status"] = update.user_status.value
    
    if update.user_notes is not None:
        updates.append("user_notes = :user_notes")
        params["user_notes"] = update.user_notes
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("user_updated_at = :updated_at")
    
    update_query = f"""
        UPDATE jobs 
        SET {", ".join(updates)}
        WHERE id = :job_id
    """
    
    db.execute(text(update_query), params)
    db.commit()
    
    # Return updated job
    return await get_job(job_id, db)


@router.post("/{job_id}/status/{status}")
async def quick_update_status(
    job_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Quick endpoint to update just the status"""
    valid_statuses = ["not_viewed", "not_applied", "applied", "interested", "not_interested", "archived"]
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    query = """
        UPDATE jobs 
        SET user_status = :status, user_updated_at = :updated_at
        WHERE id = :job_id
    """
    
    db.execute(text(query), {
        "job_id": job_id,
        "status": status,
        "updated_at": datetime.now().isoformat()
    })
    db.commit()
    
    return {"success": True, "job_id": job_id, "status": status}
