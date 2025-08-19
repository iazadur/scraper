#!/usr/bin/env python3
"""
Script to run news scraping and deduplication
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def run_full_scraping():
    """Run full scraping process"""
    logger.info("Starting full scraping process...")
    
    try:
        # Connect to database
        await db_manager.connect()
        
        # Initialize scraper manager
        scraper_manager = ScraperManager()
        
        # Scrape all sources
        logger.info("Scraping all news sources...")
        scraping_results = await scraper_manager.scrape_all_sources(limit_per_source=50)
        
        logger.info(f"Scraping completed: {scraping_results}")
        
        # Close scraper manager
        await scraper_manager.close()
        
        # Run deduplication
        logger.info("Starting deduplication process...")
        dedup_results = await deduplicator.process_raw_to_unique()
        
        logger.info(f"Deduplication completed: {dedup_results}")
        
        # Cleanup duplicates
        logger.info("Cleaning up remaining duplicates...")
        cleanup_results = await deduplicator.cleanup_duplicates_in_unique_collection()
        
        logger.info(f"Cleanup completed: {cleanup_results}")
        
        # Show final stats
        final_stats = await db_manager.get_database_stats()
        logger.info(f"Final database stats: {final_stats}")
        
        # Disconnect
        await db_manager.disconnect()
        
        logger.info("Full scraping process completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in full scraping process: {str(e)}")
        raise e

async def run_single_source(source_key: str, limit: int = 20):
    """Run scraping for a single source"""
    logger.info(f"Starting scraping for source: {source_key}")
    
    try:
        # Connect to database
        await db_manager.connect()
        
        # Initialize scraper manager
        scraper_manager = ScraperManager()
        
        # Scrape single source
        result = await scraper_manager.scrape_single_source(source_key, limit)
        
        logger.info(f"Scraping result: {result}")
        
        # Close scraper manager
        await scraper_manager.close()
        
        # Run deduplication for new data
        logger.info("Running deduplication...")
        dedup_results = await deduplicator.process_raw_to_unique()
        
        logger.info(f"Deduplication completed: {dedup_results}")
        
        # Show stats
        stats = await db_manager.get_database_stats()
        logger.info(f"Database stats: {stats}")
        
        # Disconnect
        await db_manager.disconnect()
        
        logger.info(f"Single source scraping completed for {source_key}!")
        
    except Exception as e:
        logger.error(f"Error scraping {source_key}: {str(e)}")
        raise e

async def show_available_sources():
    """Show available news sources"""
    try:
        scraper_manager = ScraperManager()
        sources = await scraper_manager.get_available_sources()
        await scraper_manager.close()
        
        print("\nAvailable News Sources:")
        print("=" * 50)
        for source in sources:
            print(f"Key: {source['key']}")
            print(f"Name: {source['name']}")
            print(f"URL: {source['base_url']}")
            print(f"RSS Feeds: {source['rss_feeds_count']}")
            print("-" * 30)
        
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")

def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  python run_scraper.py [command] [options]")
    print("\nCommands:")
    print("  full                    - Run full scraping for all sources")
    print("  source <source_key>     - Scrape single source")
    print("  sources                 - List available sources")
    print("  help                    - Show this help message")
    print("\nExamples:")
    print("  python run_scraper.py full")
    print("  python run_scraper.py source daily_star")
    print("  python run_scraper.py sources")

async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "full":
        await run_full_scraping()
    
    elif command == "source":
        if len(sys.argv) < 3:
            print("Error: Please specify source key")
            print("Use 'python run_scraper.py sources' to see available sources")
            return
        
        source_key = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        await run_single_source(source_key, limit)
    
    elif command == "sources":
        await show_available_sources()
    
    elif command == "help":
        print_usage()
    
    else:
        print(f"Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    asyncio.run(main())

