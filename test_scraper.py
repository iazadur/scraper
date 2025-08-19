#!/usr/bin/env python3
"""
Test script for Bangladesh News Scraper
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import db_manager
from scrapers.scraper_manager import ScraperManager
from utils.deduplication import deduplicator
from utils.geolocation import GeolocationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection"""
    logger.info("Testing database connection...")
    try:
        await db_manager.connect()
        stats = await db_manager.get_database_stats()
        logger.info(f"Database connected successfully. Stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

async def test_geolocation_service():
    """Test geolocation service"""
    logger.info("Testing geolocation service...")
    try:
        async with GeolocationService() as geo_service:
            # Test location extraction
            test_text = "ঢাকায় আজ একটি গুরুত্বপূর্ণ সভা অনুষ্ঠিত হয়েছে। চট্টগ্রামে নতুন প্রকল্প শুরু হবে।"
            locations = geo_service.extract_locations_from_text(test_text)
            logger.info(f"Extracted locations: {locations}")
            
            # Test geocoding
            if locations:
                lat_lng = await geo_service.geocode_location(locations[0])
                logger.info(f"Geocoded '{locations[0]}' to: {lat_lng}")
            
            # Test with sample news item
            sample_news = {
                'title': 'ঢাকায় নতুন উন্নয়ন প্রকল্প',
                'description': 'রাজধানী ঢাকার গুলশান এলাকায় একটি নতুন উন্নয়ন প্রকল্প শুরু হয়েছে।'
            }
            
            news_location = await geo_service.get_location_for_news(sample_news)
            logger.info(f"News location: {news_location}")
            
        return True
    except Exception as e:
        logger.error(f"Geolocation service test failed: {str(e)}")
        return False

async def test_single_scraper():
    """Test scraping from a single source"""
    logger.info("Testing single source scraping...")
    try:
        scraper_manager = ScraperManager()
        
        # Test scraping from Daily Star (English, likely to work)
        result = await scraper_manager.scrape_single_source('daily_star', limit=5)
        logger.info(f"Scraping result: {result}")
        
        await scraper_manager.close()
        return result['success']
    except Exception as e:
        logger.error(f"Single scraper test failed: {str(e)}")
        return False

async def test_deduplication():
    """Test deduplication process"""
    logger.info("Testing deduplication...")
    try:
        # Check if we have raw data to deduplicate
        raw_count = await db_manager.get_raw_news_count()
        logger.info(f"Raw news count: {raw_count}")
        
        if raw_count > 0:
            # Run deduplication on a small batch
            result = await deduplicator.process_raw_to_unique(batch_size=10)
            logger.info(f"Deduplication result: {result}")
            return True
        else:
            logger.info("No raw data to deduplicate")
            return True
    except Exception as e:
        logger.error(f"Deduplication test failed: {str(e)}")
        return False

async def test_api_queries():
    """Test database queries that API endpoints use"""
    logger.info("Testing API queries...")
    try:
        # Test recent news
        recent_news = await db_manager.get_recent_news(5)
        logger.info(f"Recent news count: {len(recent_news)}")
        
        # Test search
        search_results = await db_manager.search_news(query="ঢাকা", limit=5)
        logger.info(f"Search results count: {len(search_results)}")
        
        # Test source stats
        source_stats = await db_manager.get_source_stats()
        logger.info(f"Source stats: {source_stats}")
        
        # Test category stats
        category_stats = await db_manager.get_category_stats()
        logger.info(f"Category stats: {category_stats}")
        
        return True
    except Exception as e:
        logger.error(f"API queries test failed: {str(e)}")
        return False

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    logger.info("Starting comprehensive test suite...")
    
    test_results = {}
    
    # Test 1: Database connection
    test_results['database'] = await test_database_connection()
    
    # Test 2: Geolocation service
    test_results['geolocation'] = await test_geolocation_service()
    
    # Test 3: Single scraper
    test_results['scraper'] = await test_single_scraper()
    
    # Test 4: Deduplication
    test_results['deduplication'] = await test_deduplication()
    
    # Test 5: API queries
    test_results['api_queries'] = await test_api_queries()
    
    # Cleanup
    await db_manager.disconnect()
    
    # Summary
    logger.info("Test Results Summary:")
    logger.info("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name.upper()}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("All tests passed! System is ready.")
        return True
    else:
        logger.warning(f"{total - passed} tests failed. Please check the logs.")
        return False

async def quick_demo():
    """Quick demonstration of the system"""
    logger.info("Running quick demo...")
    
    try:
        await db_manager.connect()
        
        # Show current stats
        stats = await db_manager.get_database_stats()
        logger.info(f"Current database stats: {stats}")
        
        # If we have data, show some examples
        if stats['unique_news_count'] > 0:
            logger.info("Sample recent news:")
            recent = await db_manager.get_recent_news(3)
            for i, news in enumerate(recent, 1):
                logger.info(f"{i}. {news.get('title', 'No title')[:100]}...")
                logger.info(f"   Source: {news.get('source', 'Unknown')}")
                logger.info(f"   Location: {news.get('lat', 'N/A')}, {news.get('lng', 'N/A')}")
                logger.info("")
        
        await db_manager.disconnect()
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(quick_demo())
    else:
        asyncio.run(run_comprehensive_test())

