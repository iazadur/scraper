import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import NEWS_SOURCES, MONGODB_URL, DATABASE_NAME, RAW_COLLECTION
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ScraperManager:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client[DATABASE_NAME]
        self.raw_collection = self.db[RAW_COLLECTION]
        self.scrapers = {}
        
        # Initialize scrapers for each news source
        for source_key, source_config in NEWS_SOURCES.items():
            self.scrapers[source_key] = BaseScraper(source_config)
    
    async def scrape_all_sources(self, limit_per_source: Optional[int] = None) -> Dict[str, Any]:
        """Scrape news from all configured sources"""
        logger.info("Starting to scrape all news sources")
        
        results = {
            'total_articles': 0,
            'sources': {},
            'errors': [],
            'start_time': datetime.utcnow(),
            'end_time': None
        }
        
        # Create tasks for all scrapers
        tasks = []
        for source_key, scraper in self.scrapers.items():
            task = asyncio.create_task(
                self._scrape_source_with_error_handling(source_key, scraper, limit_per_source)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(source_results):
            source_key = list(self.scrapers.keys())[i]
            
            if isinstance(result, Exception):
                error_msg = f"Error scraping {source_key}: {str(result)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['sources'][source_key] = {'articles': 0, 'error': str(result)}
            else:
                articles_count = len(result)
                results['total_articles'] += articles_count
                results['sources'][source_key] = {'articles': articles_count}
                
                # Store articles in raw collection
                if result:
                    try:
                        await self.raw_collection.insert_many(result)
                        logger.info(f"Stored {articles_count} articles from {source_key}")
                    except Exception as e:
                        error_msg = f"Error storing articles from {source_key}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
        
        results['end_time'] = datetime.utcnow()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        logger.info(f"Scraping completed. Total articles: {results['total_articles']}")
        return results
    
    async def _scrape_source_with_error_handling(
        self, 
        source_key: str, 
        scraper: BaseScraper, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Scrape a single source with error handling"""
        try:
            async with scraper:
                articles = await scraper.scrape_news(limit)
                return articles
        except Exception as e:
            logger.error(f"Error scraping {source_key}: {str(e)}")
            raise e
    
    async def scrape_single_source(self, source_key: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Scrape news from a single source"""
        if source_key not in self.scrapers:
            raise ValueError(f"Unknown source: {source_key}")
        
        logger.info(f"Starting to scrape {source_key}")
        
        scraper = self.scrapers[source_key]
        start_time = datetime.utcnow()
        
        try:
            async with scraper:
                articles = await scraper.scrape_news(limit)
            
            # Store articles in raw collection
            if articles:
                await self.raw_collection.insert_many(articles)
                logger.info(f"Stored {len(articles)} articles from {source_key}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'source': source_key,
                'articles_count': len(articles),
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'success': True
            }
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            
            logger.error(f"Error scraping {source_key}: {error_msg}")
            
            return {
                'source': source_key,
                'articles_count': 0,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'success': False,
                'error': error_msg
            }
    
    async def get_available_sources(self) -> List[Dict[str, str]]:
        """Get list of available news sources"""
        sources = []
        for source_key, config in NEWS_SOURCES.items():
            sources.append({
                'key': source_key,
                'name': config['name'],
                'base_url': config['base_url'],
                'rss_feeds_count': len(config.get('rss_feeds', []))
            })
        return sources
    
    async def close(self):
        """Close database connection"""
        self.client.close()

