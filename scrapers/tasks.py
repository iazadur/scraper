import asyncio
import logging
from celery import Celery
from scrapers.scraper_manager import ScraperManager
from utils.deduplication import NewsDeduplicator
from utils.geolocation import NewsGeolocation

# Create Celery app
celery = Celery('bangladesh_news_scraper')
celery.config_from_object('celery_config')

logger = logging.getLogger(__name__)

@celery.task
def scrape_all_news():
    """Celery task to scrape news from all sources"""
    async def _scrape():
        manager = ScraperManager()
        results = await manager.scrape_all_sources()
        logger.info(f"Scraped {results['total_articles']} articles from all sources")
        
        # Run deduplication
        deduplicator = NewsDeduplicator()
        await deduplicator.deduplicate_latest_batch()
        
        # Run geolocation
        geolocator = NewsGeolocation()
        await geolocator.geolocate_latest_batch()
        
        return results
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_scrape())
    finally:
        loop.close()

@celery.task
def scrape_source(source_name: str, limit: int = None):
    """Celery task to scrape news from a specific source"""
    async def _scrape():
        manager = ScraperManager()
        results = await manager.scrape_source(source_name, limit)
        logger.info(f"Scraped {results.get('articles_scraped', 0)} articles from {source_name}")
        return results
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_scrape())
    finally:
        loop.close()

@celery.task
def deduplicate_news():
    """Celery task to deduplicate news articles"""
    async def _deduplicate():
        deduplicator = NewsDeduplicator()
        results = await deduplicator.deduplicate_all()
        logger.info(f"Deduplicated news articles: {results}")
        return results
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_deduplicate())
    finally:
        loop.close()

@celery.task
def geolocate_news():
    """Celery task to geolocate news articles"""
    async def _geolocate():
        geolocator = NewsGeolocation()
        results = await geolocator.geolocate_all()
        logger.info(f"Geolocated news articles: {results}")
        return results
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_geolocate())
    finally:
        loop.close()
