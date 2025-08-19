from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
from models.database import db_manager
from scrapers.scraper_manager import ScraperManager
from utils.deduplication import deduplicator
from config.settings import NEWS_SOURCES

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class NewsFilter(BaseModel):
    source: Optional[str] = Field(None, description="Filter by news source")
    category: Optional[str] = Field(None, description="Filter by category")
    search_text: Optional[str] = Field(None, description="Search in title and description")
    date_from: Optional[datetime] = Field(None, description="Filter news from this date")
    date_to: Optional[datetime] = Field(None, description="Filter news until this date")
    lat_min: Optional[float] = Field(None, description="Minimum latitude for geographic filter")
    lat_max: Optional[float] = Field(None, description="Maximum latitude for geographic filter")
    lng_min: Optional[float] = Field(None, description="Minimum longitude for geographic filter")
    lng_max: Optional[float] = Field(None, description="Maximum longitude for geographic filter")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    skip: int = Field(0, ge=0, description="Number of results to skip")

class GeoBounds(BaseModel):
    north: float = Field(..., description="Northern boundary latitude")
    south: float = Field(..., description="Southern boundary latitude")
    east: float = Field(..., description="Eastern boundary longitude")
    west: float = Field(..., description="Western boundary longitude")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")

class GeoRadius(BaseModel):
    lat: float = Field(..., description="Center latitude")
    lng: float = Field(..., description="Center longitude")
    radius_km: float = Field(..., gt=0, description="Radius in kilometers")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")

class ScrapingRequest(BaseModel):
    sources: Optional[List[str]] = Field(None, description="List of source keys to scrape")
    limit_per_source: Optional[int] = Field(None, description="Limit articles per source")

@router.get("/news", response_model=Dict[str, Any])
async def get_news(
    source: Optional[str] = Query(None, description="Filter by news source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search_text: Optional[str] = Query(None, description="Search in title and description"),
    date_from: Optional[datetime] = Query(None, description="Filter news from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter news until this date"),
    lat_min: Optional[float] = Query(None, description="Minimum latitude"),
    lat_max: Optional[float] = Query(None, description="Maximum latitude"),
    lng_min: Optional[float] = Query(None, description="Minimum longitude"),
    lng_max: Optional[float] = Query(None, description="Maximum longitude"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get news with advanced filtering options"""
    try:
        news_items = await db_manager.search_news(
            query=search_text,
            source=source,
            category=category,
            date_from=date_from,
            date_to=date_to,
            lat_min=lat_min,
            lat_max=lat_max,
            lng_min=lng_min,
            lng_max=lng_max,
            limit=limit,
            skip=skip
        )
        
        # Convert ObjectId to string for JSON serialization
        for item in news_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        return {
            "success": True,
            "count": len(news_items),
            "data": news_items,
            "filters": {
                "source": source,
                "category": category,
                "search_text": search_text,
                "date_from": date_from,
                "date_to": date_to,
                "geographic_bounds": {
                    "lat_min": lat_min,
                    "lat_max": lat_max,
                    "lng_min": lng_min,
                    "lng_max": lng_max
                },
                "limit": limit,
                "skip": skip
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/geo/bounds", response_model=Dict[str, Any])
async def get_news_by_bounds(
    north: float = Query(..., description="Northern boundary latitude"),
    south: float = Query(..., description="Southern boundary latitude"),
    east: float = Query(..., description="Eastern boundary longitude"),
    west: float = Query(..., description="Western boundary longitude"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """Get news within geographic bounds"""
    try:
        news_items = await db_manager.get_news_by_location_bounds(north, south, east, west, limit)
        
        # Convert ObjectId to string
        for item in news_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        return {
            "success": True,
            "count": len(news_items),
            "data": news_items,
            "bounds": {
                "north": north,
                "south": south,
                "east": east,
                "west": west
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting news by bounds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/geo/radius", response_model=Dict[str, Any])
async def get_news_by_radius(
    lat: float = Query(..., description="Center latitude"),
    lng: float = Query(..., description="Center longitude"),
    radius_km: float = Query(..., gt=0, description="Radius in kilometers"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """Get news within radius of a point"""
    try:
        news_items = await db_manager.get_news_in_radius(lat, lng, radius_km, limit)
        
        # Convert ObjectId to string
        for item in news_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        return {
            "success": True,
            "count": len(news_items),
            "data": news_items,
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km
        }
        
    except Exception as e:
        logger.error(f"Error getting news by radius: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/recent", response_model=Dict[str, Any])
async def get_recent_news(
    limit: int = Query(50, ge=1, le=500, description="Number of recent news items")
):
    """Get most recent news items"""
    try:
        news_items = await db_manager.get_recent_news(limit)
        
        # Convert ObjectId to string
        for item in news_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        return {
            "success": True,
            "count": len(news_items),
            "data": news_items
        }
        
    except Exception as e:
        logger.error(f"Error getting recent news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = await db_manager.get_database_stats()
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources", response_model=Dict[str, Any])
async def get_available_sources():
    """Get list of available news sources"""
    try:
        scraper_manager = ScraperManager()
        sources = await scraper_manager.get_available_sources()
        await scraper_manager.close()
        
        return {
            "success": True,
            "count": len(sources),
            "data": sources
        }
        
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape", response_model=Dict[str, Any])
async def start_scraping(
    background_tasks: BackgroundTasks,
    request: ScrapingRequest = ScrapingRequest()
):
    """Start scraping news from specified sources"""
    try:
        scraper_manager = ScraperManager()
        
        if request.sources:
            # Validate source keys
            invalid_sources = [s for s in request.sources if s not in NEWS_SOURCES]
            if invalid_sources:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid sources: {invalid_sources}"
                )
            
            # Start scraping in background
            background_tasks.add_task(
                scrape_sources_background,
                request.sources,
                request.limit_per_source
            )
            
            return {
                "success": True,
                "message": f"Started scraping {len(request.sources)} sources",
                "sources": request.sources
            }
        else:
            # Scrape all sources
            background_tasks.add_task(
                scrape_all_sources_background,
                request.limit_per_source
            )
            
            return {
                "success": True,
                "message": "Started scraping all sources",
                "sources": list(NEWS_SOURCES.keys())
            }
        
    except Exception as e:
        logger.error(f"Error starting scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deduplicate", response_model=Dict[str, Any])
async def start_deduplication(background_tasks: BackgroundTasks):
    """Start deduplication process"""
    try:
        background_tasks.add_task(deduplication_background)
        
        return {
            "success": True,
            "message": "Started deduplication process"
        }
        
    except Exception as e:
        logger.error(f"Error starting deduplication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/categories", response_model=Dict[str, Any])
async def get_categories():
    """Get available news categories"""
    try:
        category_stats = await db_manager.get_category_stats()
        categories = [stat['category'] for stat in category_stats if stat['category']]
        
        return {
            "success": True,
            "count": len(categories),
            "data": categories,
            "stats": category_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/map-data", response_model=Dict[str, Any])
async def get_map_data(
    bounds: Optional[str] = Query(None, description="Geographic bounds as 'north,south,east,west'"),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum number of results")
):
    """Get news data optimized for map visualization"""
    try:
        if bounds:
            # Parse bounds
            try:
                north, south, east, west = map(float, bounds.split(','))
                news_items = await db_manager.get_news_by_location_bounds(north, south, east, west, limit)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bounds format. Use 'north,south,east,west'")
        else:
            # Get all geolocated news
            news_items = await db_manager.search_news(
                lat_min=-90, lat_max=90, lng_min=-180, lng_max=180, limit=limit
            )
        
        # Format for map display
        map_data = []
        for item in news_items:
            if item.get('lat') and item.get('lng'):
                map_data.append({
                    'id': str(item['_id']),
                    'title': item.get('title', ''),
                    'description': item.get('description', '')[:200] + '...' if len(item.get('description', '')) > 200 else item.get('description', ''),
                    'source': item.get('source', ''),
                    'category': item.get('category', ''),
                    'lat': item['lat'],
                    'lng': item['lng'],
                    'published_date': item.get('published_date'),
                    'source_url': item.get('source_url', ''),
                    'image_url': item.get('image_url', '')
                })
        
        return {
            "success": True,
            "count": len(map_data),
            "data": map_data,
            "bounds": bounds
        }
        
    except Exception as e:
        logger.error(f"Error getting map data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def scrape_sources_background(sources: List[str], limit_per_source: Optional[int]):
    """Background task for scraping specific sources"""
    try:
        scraper_manager = ScraperManager()
        
        for source in sources:
            logger.info(f"Starting background scraping for {source}")
            result = await scraper_manager.scrape_single_source(source, limit_per_source)
            logger.info(f"Completed scraping {source}: {result}")
        
        await scraper_manager.close()
        logger.info("Background scraping completed")
        
    except Exception as e:
        logger.error(f"Error in background scraping: {str(e)}")

async def scrape_all_sources_background(limit_per_source: Optional[int]):
    """Background task for scraping all sources"""
    try:
        scraper_manager = ScraperManager()
        logger.info("Starting background scraping for all sources")
        
        result = await scraper_manager.scrape_all_sources(limit_per_source)
        logger.info(f"Completed scraping all sources: {result}")
        
        await scraper_manager.close()
        logger.info("Background scraping completed")
        
    except Exception as e:
        logger.error(f"Error in background scraping: {str(e)}")

async def deduplication_background():
    """Background task for deduplication"""
    try:
        logger.info("Starting background deduplication")
        
        # Process raw to unique
        result = await deduplicator.process_raw_to_unique()
        logger.info(f"Deduplication result: {result}")
        
        # Cleanup any remaining duplicates
        cleanup_result = await deduplicator.cleanup_duplicates_in_unique_collection()
        logger.info(f"Cleanup result: {cleanup_result}")
        
        logger.info("Background deduplication completed")
        
    except Exception as e:
        logger.error(f"Error in background deduplication: {str(e)}")

