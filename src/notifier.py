import os
import asyncio
from typing import List, Optional
from datetime import datetime
import aiohttp
from src.utils.logger import get_logger

logger = get_logger()


class TelegramNotifier:
    """Send job notifications via Telegram."""
    
    def __init__(self, config: dict):
        self.config = config
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        
        notification_config = config.get('notification', {}).get('telegram', {})
        self.max_message_length = notification_config.get('max_message_length', 4000)
        self.max_jobs_per_message = notification_config.get('max_jobs_per_message', 15)
    
    def _validate_config(self) -> bool:
        """Validate that Telegram credentials are available."""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials not configured")
            return False
        return True
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a single message to Telegram."""
        if not self._validate_config():
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.debug("Message sent successfully")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Telegram API error: {error}")
                        return False
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def format_job_card(self, job: dict) -> str:
        """Format a single job as a card."""
        # Star rating based on score
        score = job.get('total_score', 0)
        if score >= 8:
            stars = "⭐⭐⭐"
        elif score >= 6:
            stars = "⭐⭐"
        elif score >= 4:
            stars = "⭐"
        else:
            stars = ""
        
        # Build card
        card = f"📊 <b>Score: {score:.1f}/10</b> {stars}\n"
        card += f"<b>{self._escape_html(job['title'])}</b>\n"
        card += f"🏢 {self._escape_html(job['company'])}\n"
        card += f"📍 {self._escape_html(job['location'])}\n"
        
        if job.get('salary_text'):
            card += f"💰 {self._escape_html(job['salary_text'])}\n"
        
        card += f"🔗 <a href=\"{job['url']}\">Apply</a>\n"
        
        # Tags/indicators
        indicators = []
        if job.get('passion_score', 0) >= 6:
            indicators.append("🤖 ML/AI")
        if job.get('location_score', 0) >= 8:
            indicators.append("📍 Preferred Location")
        if job.get('money_score', 0) >= 7:
            indicators.append("💰 Good Pay")
        
        if indicators:
            card += f"💡 {' | '.join(indicators)}\n"
        
        if job.get('posted_date'):
            card += f"📅 Posted: {job['posted_date']}\n"
        
        return card
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
    
    def chunk_jobs(self, jobs: List[dict]) -> List[str]:
        """Split jobs into message chunks that fit Telegram limits."""
        chunks = []
        current_chunk = ""
        current_job_count = 0
        
        header = f"🎯 <b>Daily Job Report - {datetime.now().strftime('%B %d, %Y')}</b>\n"
        header += f"Found <b>{len(jobs)} new jobs</b> matching your criteria!\n\n"
        header += "━" * 20 + "\n\n"
        
        current_chunk = header
        
        for job in jobs:
            job_card = self.format_job_card(job)
            job_card += "\n" + "━" * 20 + "\n\n"
            
            # Check if adding this job would exceed limits
            if (len(current_chunk) + len(job_card) > self.max_message_length or 
                current_job_count >= self.max_jobs_per_message):
                # Save current chunk and start new one
                chunks.append(current_chunk)
                current_chunk = f"📋 <b>Continued...</b> (Jobs {current_job_count + 1}+)\n\n"
                current_chunk += "━" * 20 + "\n\n"
                current_job_count = 0
            
            current_chunk += job_card
            current_job_count += 1
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def send_job_report(self, jobs: List[dict], errors: List[str] = None) -> bool:
        """Send the full job report, chunked if necessary."""
        if not jobs and not errors:
            logger.info("No jobs to send")
            return True
        
        success = True
        
        # Send job chunks
        if jobs:
            chunks = self.chunk_jobs(jobs)
            logger.info(f"Sending {len(jobs)} jobs in {len(chunks)} message(s)")
            
            for i, chunk in enumerate(chunks):
                if not await self.send_message(chunk):
                    success = False
                # Rate limiting between messages
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
            
            # Send summary
            summary = self._create_summary(jobs)
            await self.send_message(summary)
        
        # Send error notification if there were errors
        if errors:
            error_msg = self._format_errors(errors)
            await self.send_message(error_msg)
        
        return success
    
    def _create_summary(self, jobs: List[dict]) -> str:
        """Create a summary message."""
        summary = "📈 <b>Summary:</b>\n\n"
        summary += f"✅ {len(jobs)} new jobs found\n"
        
        # Count by criteria
        ml_count = sum(1 for j in jobs if j.get('passion_score', 0) >= 5)
        bavaria_count = sum(1 for j in jobs if j.get('location_score', 0) >= 10)
        germany_count = sum(1 for j in jobs if j.get('location_score', 0) >= 6)
        salary_count = sum(1 for j in jobs if j.get('salary_min'))
        
        summary += f"🤖 {ml_count} ML/AI focused\n"
        summary += f"📍 {bavaria_count} in Bavaria, {germany_count} in Germany\n"
        summary += f"💰 {salary_count} with salary info\n"
        
        if jobs:
            top_score = max(j.get('total_score', 0) for j in jobs)
            avg_score = sum(j.get('total_score', 0) for j in jobs) / len(jobs)
            summary += f"🏆 Top score: {top_score:.1f}/10\n"
            summary += f"📊 Average score: {avg_score:.1f}/10\n"
        
        # Count by platform
        platforms = {}
        for job in jobs:
            p = job.get('platform', 'unknown')
            platforms[p] = platforms.get(p, 0) + 1
        
        platform_str = ", ".join(f"{p.title()} ({c})" for p, c in platforms.items())
        summary += f"\n🔍 Sources: {platform_str}\n"
        summary += "\n#JobHunt #DataScience"
        
        return summary
    
    def _format_errors(self, errors: List[str]) -> str:
        """Format error messages."""
        msg = "⚠️ <b>Job Scraper Alert</b>\n\n"
        msg += "Scraping completed with errors:\n\n"
        
        for error in errors:
            msg += f"❌ {self._escape_html(error)}\n"
        
        msg += "\nCheck logs for details."
        return msg
    
    def send_sync(self, jobs: List[dict], errors: List[str] = None) -> bool:
        """Synchronous wrapper for send_job_report."""
        return asyncio.run(self.send_job_report(jobs, errors))
