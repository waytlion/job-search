"""
FastAPI Backend for Job Scraper Web Application
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routes import jobs, stats, config, sync, filters
from app.database.connection import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield

app = FastAPI(
    title="Job Scraper API",
    description="API for the Job Scraper Web Application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(stats.router)
app.include_router(config.router)
app.include_router(sync.router)
app.include_router(filters.router)

@app.get("/")
async def root():
    return {"message": "Job Scraper API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
