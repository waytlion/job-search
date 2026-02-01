"""Sync API routes - for syncing with GitHub Actions"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os

from app.database.connection import get_db
from app.models.config import SyncResponse

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
async def trigger_sync(db: Session = Depends(get_db)):
    """
    Trigger a sync with GitHub Actions artifacts.
    Note: For local development, this just returns the current state.
    In production, this would download the latest jobs.db artifact.
    """
    errors = []
    new_jobs = 0
    
    # For now, just record the sync attempt
    # In production, this would:
    # 1. Download latest artifact from GitHub
    # 2. Import new jobs into the database
    # 3. Return the count of new jobs
    
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    
    if not github_token or not github_repo:
        errors.append("GitHub credentials not configured. Set GITHUB_TOKEN and GITHUB_REPO in .env")
    
    # Record sync in history
    db.execute(text("""
        INSERT INTO sync_history (jobs_imported, source, errors)
        VALUES (:jobs, :source, :errors)
    """), {
        "jobs": new_jobs,
        "source": "manual",
        "errors": str(errors) if errors else None
    })
    db.commit()
    
    return SyncResponse(
        success=len(errors) == 0,
        newJobs=new_jobs,
        lastSync=datetime.now().isoformat(),
        errors=errors
    )


@router.get("/history")
async def get_sync_history(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get sync history"""
    result = db.execute(text("""
        SELECT id, timestamp, jobs_imported, source, errors
        FROM sync_history
        ORDER BY timestamp DESC
        LIMIT :limit
    """), {"limit": limit})
    
    history = []
    for row in result.fetchall():
        history.append({
            "id": row[0],
            "timestamp": row[1],
            "jobs_imported": row[2],
            "source": row[3],
            "errors": row[4]
        })
    
    return {"history": history}
