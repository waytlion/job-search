from typing import List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import html2text
from .base import BaseScraper, Job, resilient_request
from src.utils.logger import get_logger

logger = get_logger()


class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for We Work Remotely RSS feeds — no API key needed."""
    
    # RSS feeds for relevant categories
    DEFAULT_FEEDS = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    ]
    
    @property
    def platform_name(self) -> str:
        return "weworkremotely"
    
    def scrape(self) -> List[Job]:
        """Scrape jobs from WWR RSS feeds."""
        if not self.is_enabled():
            logger.info("WeWorkRemotely scraper is disabled")
            return []
        
        logger.info("🏠 Starting WeWorkRemotely scraper...")
        
        wwr_config = self.config.get('scraping', {}).get('weworkremotely', {})
        feeds = wwr_config.get('feeds', self.DEFAULT_FEEDS)
        
        all_jobs = []
        seen_hashes = set()
        
        for feed_url in feeds:
            try:
                jobs = self._fetch_feed(feed_url)
                for job in jobs:
                    if job.job_hash not in seen_hashes:
                        seen_hashes.add(job.job_hash)
                        all_jobs.append(job)
            except Exception as e:
                error_msg = f"Error fetching feed {feed_url}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        logger.info(f"   ✅ WeWorkRemotely: Found {len(all_jobs)} unique jobs")
        self.jobs = all_jobs
        return all_jobs
    
    def _fetch_feed(self, feed_url: str) -> List[Job]:
        """Fetch and parse an RSS feed."""
        response = resilient_request(
            feed_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; JobScraper/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml',
            },
            timeout=30,
            platform_name=self.platform_name,
        )
        
        if response is None:
            return []
        
        jobs = []
        try:
            root = ET.fromstring(response.content)
            # RSS 2.0 format: <channel><item>...</item></channel>
            channel = root.find('channel')
            if channel is None:
                return []
            
            for item_elem in channel.findall('item'):
                job = self._parse_item(item_elem)
                if job:
                    jobs.append(job)
        except ET.ParseError as e:
            logger.warning(f"[{self.platform_name}] XML parse error: {e}")
        
        return jobs
    
    def _parse_item(self, item: ET.Element) -> Optional[Job]:
        """Parse a single RSS item into a Job."""
        try:
            title_raw = item.findtext('title', 'Unknown Title')
            
            # WWR titles are typically: "Company: Job Title"
            if ':' in title_raw:
                parts = title_raw.split(':', 1)
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                title = title_raw
                company = 'Unknown Company'
            
            url = item.findtext('link', '')
            
            # Description
            description = None
            raw_desc = item.findtext('description', '')
            if raw_desc:
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                description = h.handle(raw_desc)[:2000]
            
            # Date
            posted_date = None
            pub_date = item.findtext('pubDate', '')
            if pub_date:
                try:
                    # RSS date format: "Thu, 27 Feb 2026 08:00:00 +0000"
                    dt = datetime.strptime(pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                    posted_date = dt.strftime('%Y-%m-%d')
                except:
                    try:
                        posted_date = pub_date[:10]
                    except:
                        pass
            
            # Categories as tags
            tags = [cat.text for cat in item.findall('category') if cat.text]
            
            # WWR is fully remote
            location = 'Remote'
            
            # Try to extract location hints from description/title
            for region in ['Europe', 'EU', 'EMEA', 'US', 'USA', 'Americas', 'APAC',
                          'Germany', 'UK', 'Worldwide', 'Global']:
                if region.lower() in (title + ' ' + (description or '')).lower():
                    location = f"Remote ({region})"
                    break
            
            return Job(
                title=title,
                company=company,
                location=location,
                url=url,
                platform='weworkremotely',
                description=description,
                tags=tags,
                posted_date=posted_date,
            )
        except Exception as e:
            logger.debug(f"Failed to parse WWR item: {e}")
            return None
