import sqlite3
from typing import List, Optional, Set
from datetime import datetime, timedelta
from src.scrapers.base import Job
from src.utils.logger import get_logger

logger = get_logger()


class JobDatabase:
    """SQLite database for storing and managing jobs."""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_hash TEXT UNIQUE NOT NULL,
        
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        url TEXT NOT NULL,
        platform TEXT NOT NULL,
        
        description TEXT,
        requirements TEXT,
        tags TEXT,
        
        salary_min INTEGER,
        salary_max INTEGER,
        salary_currency TEXT,
        salary_text TEXT,
        
        posted_date TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        money_score REAL,
        passion_score REAL,
        location_score REAL,
        total_score REAL,
        
        sent_to_user BOOLEAN DEFAULT 0,
        sent_at TIMESTAMP,
        
        years_experience_required INTEGER,
        filtered_out BOOLEAN DEFAULT 0,
        filter_reason TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_job_hash ON jobs(job_hash);
    CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at);
    CREATE INDEX IF NOT EXISTS idx_sent_to_user ON jobs(sent_to_user);
    CREATE INDEX IF NOT EXISTS idx_total_score ON jobs(total_score DESC);
    CREATE INDEX IF NOT EXISTS idx_platform ON jobs(platform);
    """
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
        logger.debug(f"Database initialized at {self.db_path}")
    
    def get_existing_hashes(self) -> Set[str]:
        """Get all existing job hashes for deduplication."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT job_hash FROM jobs")
            return {row[0] for row in cursor.fetchall()}
    
    def insert_jobs(self, jobs: List[Job]) -> int:
        """Insert new jobs into the database. Returns count of inserted jobs."""
        existing_hashes = self.get_existing_hashes()
        new_jobs = [j for j in jobs if j.job_hash not in existing_hashes]
        
        if not new_jobs:
            logger.info("No new jobs to insert")
            return 0
        
        with sqlite3.connect(self.db_path) as conn:
            for job in new_jobs:
                try:
                    conn.execute("""
                        INSERT INTO jobs (
                            job_hash, title, company, location, url, platform,
                            description, requirements, tags,
                            salary_min, salary_max, salary_currency, salary_text,
                            posted_date, scraped_at,
                            money_score, passion_score, location_score, total_score,
                            years_experience_required, filtered_out, filter_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job.job_hash, job.title, job.company, job.location, job.url, job.platform,
                        job.description, job.requirements, ','.join(job.tags) if job.tags else None,
                        job.salary_min, job.salary_max, job.salary_currency, job.salary_text,
                        job.posted_date, job.scraped_at.isoformat(),
                        job.money_score, job.passion_score, job.location_score, job.total_score,
                        job.years_experience_required, job.filtered_out, job.filter_reason
                    ))
                except sqlite3.IntegrityError:
                    # Duplicate, skip
                    continue
            conn.commit()
        
        logger.info(f"Inserted {len(new_jobs)} new jobs")
        return len(new_jobs)
    
    def get_unsent_jobs(self) -> List[dict]:
        """Get all jobs that haven't been sent to user yet."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM jobs 
                WHERE sent_to_user = 0 AND filtered_out = 0
                ORDER BY total_score DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_jobs_as_sent(self, job_hashes: List[str]):
        """Mark jobs as sent to user."""
        if not job_hashes:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join(['?' for _ in job_hashes])
            conn.execute(f"""
                UPDATE jobs 
                SET sent_to_user = 1, sent_at = ?
                WHERE job_hash IN ({placeholders})
            """, [datetime.now().isoformat()] + job_hashes)
            conn.commit()
        
        logger.info(f"Marked {len(job_hashes)} jobs as sent")
    
    def cleanup_old_jobs(self, retention_days: int = 90):
        """Remove jobs older than retention period."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM jobs WHERE scraped_at < ?",
                [cutoff.isoformat()]
            )
            deleted = cursor.rowcount
            conn.commit()
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old jobs")
        
        return deleted
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Total jobs
            cursor = conn.execute("SELECT COUNT(*) FROM jobs")
            stats['total_jobs'] = cursor.fetchone()[0]
            
            # Unsent jobs
            cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE sent_to_user = 0 AND filtered_out = 0")
            stats['unsent_jobs'] = cursor.fetchone()[0]
            
            # Jobs by platform
            cursor = conn.execute("SELECT platform, COUNT(*) FROM jobs GROUP BY platform")
            stats['by_platform'] = dict(cursor.fetchall())
            
            # Filtered jobs
            cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE filtered_out = 1")
            stats['filtered_jobs'] = cursor.fetchone()[0]
            
            return stats
