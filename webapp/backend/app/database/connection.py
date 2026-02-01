"""Database connection and session management"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get database path - default to parent jobs.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../jobs.db")

# Handle relative paths for SQLite
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        # Make path relative to this file's directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.normpath(os.path.join(base_dir, db_path))
        DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with new columns if needed"""
    with engine.connect() as conn:
        # Check if user_status column exists
        result = conn.execute(text("PRAGMA table_info(jobs)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add new columns if they don't exist
        if 'user_status' not in columns:
            conn.execute(text(
                "ALTER TABLE jobs ADD COLUMN user_status TEXT DEFAULT 'not_viewed'"
            ))
            print("Added user_status column")
        
        if 'user_notes' not in columns:
            conn.execute(text(
                "ALTER TABLE jobs ADD COLUMN user_notes TEXT"
            ))
            print("Added user_notes column")
        
        if 'user_updated_at' not in columns:
            conn.execute(text(
                "ALTER TABLE jobs ADD COLUMN user_updated_at TIMESTAMP"
            ))
            print("Added user_updated_at column")
        
        conn.commit()
        
        # Create sync_history table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                jobs_imported INTEGER,
                source TEXT,
                errors TEXT
            )
        """))
        conn.commit()
        
        # Create config_snapshots table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS config_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                config TEXT,
                description TEXT
            )
        """))
        conn.commit()
        
    print(f"Database initialized: {DATABASE_URL}")
