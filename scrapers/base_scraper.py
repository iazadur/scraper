import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
from urllib.parse import urljoin, urlparse
import re
from dateutil import parser as date_parser
import pytz

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.name = source_config["name"]
        self.base_url = source_config["base_url"]
        self.rss_feeds = source_config.get("rss_feeds", [])
        self.selectors = source_config.get("selectors", {})
        self.session = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    async def parse_rss_feeds(self) -> List[Dict[str, Any]]:
        """Parse RSS feeds to get article URLs"""
        articles = []
        
        for feed_url in self.rss_feeds:
            try:
                content = await self.fetch_url(feed_url)
                if content:
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries:
                        article = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', ''),
                            'published_date': self._parse_date(entry.get('published', '')),
                            'source': self.name,
                            'category': self._extract_category(entry.get('link', ''))
                        }
                        
                        if article['url']:
                            articles.append(article)
                            
            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
                
        return articles
    
    async def scrape_article_details(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape detailed content from article URL"""
        try:
            content = await self.fetch_url(article['url'])
            if not content:
                return article
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title if not from RSS
            if not article.get('title'):
                title_elem = soup.select_one(self.selectors.get('title', 'h1'))
                if title_elem:
                    article['title'] = title_elem.get_text(strip=True)
            
            # Extract description/content
            description_parts = []
            description_elems = soup.select(self.selectors.get('description', 'p'))
            for elem in description_elems[:5]:  # Limit to first 5 paragraphs
                text = elem.get_text(strip=True)
                if text and len(text) > 20:  # Filter out short/empty paragraphs
                    description_parts.append(text)
            
            if description_parts:
                article['description'] = ' '.join(description_parts)
            
            # Extract image URL
            img_elem = soup.select_one(self.selectors.get('image', 'img'))
            if img_elem:
                img_src = img_elem.get('src') or img_elem.get('data-src')
                if img_src:
                    article['image_url'] = urljoin(article['url'], img_src)
            
            # Extract published date if not from RSS
            if not article.get('published_date'):
                date_elem = soup.select_one(self.selectors.get('date', '.date'))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    article['published_date'] = self._parse_date(date_text)
            
            # Add metadata
            article['scraped_date'] = datetime.utcnow()
            article['source_url'] = article['url']
            
            return article
            
        except Exception as e:
            logger.error(f"Error scraping article {article.get('url', '')}: {str(e)}")
            return article
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
            
        try:
            # Try parsing with dateutil
            parsed_date = date_parser.parse(date_string)
            
            # Convert to UTC if timezone aware
            if parsed_date.tzinfo:
                parsed_date = parsed_date.astimezone(pytz.UTC).replace(tzinfo=None)
            
            return parsed_date
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_string}': {str(e)}")
            return None
    
    def _extract_category(self, url: str) -> Optional[str]:
        """Extract category from URL path"""
        try:
            parsed_url = urlparse(url)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            
            # Common category patterns
            categories = ['national', 'international', 'sports', 'entertainment', 
                         'business', 'technology', 'politics', 'world', 'bangladesh',
                         'economy', 'opinion', 'lifestyle', 'health']
            
            for part in path_parts:
                if part.lower() in categories:
                    return part.lower()
                    
            return None
            
        except Exception:
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Bengali characters
        text = re.sub(r'[^\w\s\u0980-\u09FF.,!?;:()\-\'\"]+', '', text)
        
        return text.strip()
    
    async def scrape_news(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Main method to scrape news from this source"""
        logger.info(f"Starting to scrape news from {self.name}")
        
        # Get articles from RSS feeds
        articles = await self.parse_rss_feeds()
        
        if limit:
            articles = articles[:limit]
        
        # Scrape detailed content for each article
        detailed_articles = []
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def scrape_with_semaphore(article):
            async with semaphore:
                return await self.scrape_article_details(article)
        
        tasks = [scrape_with_semaphore(article) for article in articles]
        detailed_articles = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and invalid articles
        valid_articles = []
        for article in detailed_articles:
            if isinstance(article, dict) and article.get('title') and article.get('url'):
                valid_articles.append(article)
        
        logger.info(f"Scraped {len(valid_articles)} articles from {self.name}")
        return valid_articles

