#!/usr/bin/env python3
"""
Job Scraper - Main Entry Point

Scrapes jobs from multiple sources, scores them, and sends Telegram notifications.
"""

import os
import sys
import argparse
import yaml
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from src.utils.logger import setup_logger
from src.scrapers import (
    BundesagenturScraper, ArbeitnowScraper, RemoteOKScraper,
    JobicyScraper, TheMuseScraper, WeWorkRemotelyScraper, AdzunaScraper,
)
from src.filters import RelevanceFilter, ExperienceFilter
from src.scorer import JobScorer
from src.database import JobDatabase
from src.notifier import TelegramNotifier


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main(test_mode: bool = False):
    """Main execution function."""
    
    # Setup
    logger = setup_logger("job_scraper", "DEBUG" if test_mode else "INFO")
    logger.info("🚀 Starting Job Scraper...")
    logger.info(f"   Mode: {'TEST' if test_mode else 'PRODUCTION'}")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    try:
        config = load_config()
        logger.info("   ✅ Configuration loaded")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Initialize components
    db = JobDatabase(config.get('database', {}).get('path', 'jobs.db'))
    notifier = TelegramNotifier(config)
    
    # Initialize ALL scrapers — each is modular and isolated
    scrapers = [
        BundesagenturScraper(config),
        ArbeitnowScraper(config),
        RemoteOKScraper(config),
        JobicyScraper(config),
        TheMuseScraper(config),
        WeWorkRemotelyScraper(config),
        AdzunaScraper(config),
    ]
    
    # Initialize filters
    relevance_filter = RelevanceFilter(config)
    experience_filter = ExperienceFilter(config)
    
    # Initialize scorer
    scorer = JobScorer(config)
    
    # Collect all errors
    all_errors = []
    
    # Step 1: Scrape jobs from all sources (resilient — never crashes)
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 1: SCRAPING")
    logger.info("=" * 50)
    
    all_jobs = []
    for scraper in scrapers:
        # safe_scrape() catches ALL exceptions — pipeline always continues
        jobs = scraper.safe_scrape()
        all_jobs.extend(jobs)
        all_errors.extend(scraper.errors)
        if jobs:
            logger.info(f"   ✅ {scraper.platform_name}: {len(jobs)} jobs")
        elif scraper.errors:
            logger.warning(f"   ⚠️ {scraper.platform_name}: failed ({len(scraper.errors)} errors)")
    
    logger.info(f"\n📊 Total scraped: {len(all_jobs)} jobs from all sources")
    
    if not all_jobs:
        logger.warning("No jobs scraped. Sending error notification.")
        notifier.send_sync([], all_errors)
        return
    
    # Step 2: Apply filters
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 2: FILTERING")
    logger.info("=" * 50)
    
    all_jobs = relevance_filter.filter(all_jobs)
    all_jobs = experience_filter.filter(all_jobs)
    
    # Step 3: Score jobs
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 3: SCORING")
    logger.info("=" * 50)
    
    all_jobs = scorer.score_jobs(all_jobs)
    
    # Step 4: Check for duplicates and insert new jobs
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 4: DATABASE OPERATIONS")
    logger.info("=" * 50)
    
    # Filter out already filtered jobs before database
    valid_jobs = [j for j in all_jobs if not j.filtered_out]
    logger.info(f"Valid jobs after filtering: {len(valid_jobs)}")
    
    new_count = db.insert_jobs(all_jobs)  # Insert all, including filtered (for tracking)
    
    # Step 5: Get unsent jobs and send notifications
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 5: NOTIFICATIONS")
    logger.info("=" * 50)
    
    unsent_jobs = db.get_unsent_jobs()  # Already sorted by total_score DESC
    logger.info(f"Unsent jobs to notify: {len(unsent_jobs)}")
    
    if unsent_jobs or all_errors:
        # Determine how many top jobs to send via Telegram
        telegram_limit = config.get('notification', {}).get('telegram', {}).get('daily_top_n', 15)
        
        if test_mode:
            telegram_limit = min(telegram_limit, 15)
            logger.info(f"Test mode: limiting Telegram to {telegram_limit} jobs")
        
        # Only the top N jobs go to Telegram
        telegram_jobs = unsent_jobs[:telegram_limit]
        logger.info(f"📱 Telegram digest: top {len(telegram_jobs)} of {len(unsent_jobs)} unsent jobs")
        
        success = notifier.send_sync(telegram_jobs, all_errors if all_errors else None)
        
        if success:
            # Mark ALL unsent jobs as sent (not just the ones sent to Telegram)
            # This prevents them from piling up for the next run.
            # All jobs remain visible on the webapp regardless.
            all_hashes = [j['job_hash'] for j in unsent_jobs]
            db.mark_jobs_as_sent(all_hashes)
            logger.info(f"Marked all {len(unsent_jobs)} jobs as sent (Telegram received top {len(telegram_jobs)})")
    else:
        logger.info("No new jobs to send")
    
    # Step 6: Cleanup old jobs
    retention_days = config.get('database', {}).get('retention_days', 90)
    db.cleanup_old_jobs(retention_days)
    
    # Print final stats
    stats = db.get_stats()
    logger.info("\n" + "=" * 50)
    logger.info("FINAL STATS")
    logger.info("=" * 50)
    logger.info(f"   Total jobs in DB: {stats['total_jobs']}")
    logger.info(f"   Unsent jobs: {stats['unsent_jobs']}")
    logger.info(f"   Filtered jobs: {stats['filtered_jobs']}")
    logger.info(f"   By platform: {stats['by_platform']}")
    
    logger.info("\n✅ Job Scraper completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Scraper")
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run in test mode (limited results)"
    )
    args = parser.parse_args()
    
    # Check for TEST_MODE environment variable too
    test_mode = args.test or os.environ.get('TEST_MODE', 'false').lower() == 'true'
    
    main(test_mode=test_mode)
