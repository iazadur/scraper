from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from config.settings import MONGODB_URL, DATABASE_NAME, RAW_COLLECTION, UNIQUE_COLLECTION

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.raw_collection: Optional[AsyncIOMotorCollection] = None
        self.unique_collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            self.raw_collection = self.db[RAW_COLLECTION]
            self.unique_collection = self.db[UNIQUE_COLLECTION]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise e
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # Indexes for raw collection
            raw_indexes = [
                IndexModel([("source_url", ASCENDING)]),
                IndexModel([("source", ASCENDING)]),
                IndexModel([("scraped_date", DESCENDING)]),
                IndexModel([("published_date", DESCENDING)]),
                IndexModel([("title", TEXT), ("description", TEXT)]),
            ]
            
            await self.raw_collection.create_indexes(raw_indexes)
            logger.info("Created indexes for raw collection")
            
            # Indexes for unique collection
            unique_indexes = [
                IndexModel([("source_url", ASCENDING)], unique=True),
                IndexModel([("source", ASCENDING)]),
                IndexModel([("category", ASCENDING)]),
                IndexModel([("published_date", DESCENDING)]),
                IndexModel([("scraped_date", DESCENDING)]),
                IndexModel([("lat", ASCENDING), ("lng", ASCENDING)]),
                IndexModel([("title", TEXT), ("description", TEXT)]),
                IndexModel([("tags", ASCENDING)]),
                # Compound indexes for common queries
                IndexModel([("source", ASCENDING), ("published_date", DESCENDING)]),
                IndexModel([("category", ASCENDING), ("published_date", DESCENDING)]),
                IndexModel([("lat", ASCENDING), ("lng", ASCENDING), ("published_date", DESCENDING)]),
            ]
            
            await self.unique_collection.create_indexes(unique_indexes)
            logger.info("Created indexes for unique collection")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            raise e
    
    async def insert_raw_news(self, news_items: List[Dict[str, Any]]) -> int:
        """Insert news items into raw collection"""
        try:
            if not news_items:
                return 0
            
            result = await self.raw_collection.insert_many(news_items)
            inserted_count = len(result.inserted_ids)
            logger.info(f"Inserted {inserted_count} items into raw collection")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Failed to insert raw news: {str(e)}")
            raise e
    
    async def insert_unique_news(self, news_item: Dict[str, Any]) -> bool:
        """Insert news item into unique collection (with duplicate handling)"""
        try:
            await self.unique_collection.insert_one(news_item)
            return True
            
        except Exception as e:
            if "duplicate key error" in str(e).lower():
                logger.debug(f"Duplicate news item skipped: {news_item.get('source_url', 'Unknown URL')}")
                return False
            else:
                logger.error(f"Failed to insert unique news: {str(e)}")
                raise e
    
    async def get_raw_news_count(self) -> int:
        """Get count of raw news items"""
        return await self.raw_collection.count_documents({})
    
    async def get_unique_news_count(self) -> int:
        """Get count of unique news items"""
        return await self.unique_collection.count_documents({})
    
    async def get_source_stats(self) -> List[Dict[str, Any]]:
        """Get statistics by source"""
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": DESCENDING}},
            {"$project": {"source": "$_id", "count": 1, "_id": 0}}
        ]
        
        cursor = self.unique_collection.aggregate(pipeline)
        return await cursor.to_list(None)
    
    async def get_category_stats(self) -> List[Dict[str, Any]]:
        """Get statistics by category"""
        pipeline = [
            {"$match": {"category": {"$ne": None}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": DESCENDING}},
            {"$project": {"category": "$_id", "count": 1, "_id": 0}}
        ]
        
        cursor = self.unique_collection.aggregate(pipeline)
        return await cursor.to_list(None)
    
    async def get_recent_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent news items"""
        cursor = self.unique_collection.find().sort("published_date", DESCENDING).limit(limit)
        return await cursor.to_list(None)
    
    async def search_news(self, 
                         query: Optional[str] = None,
                         source: Optional[str] = None,
                         category: Optional[str] = None,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None,
                         lat_min: Optional[float] = None,
                         lat_max: Optional[float] = None,
                         lng_min: Optional[float] = None,
                         lng_max: Optional[float] = None,
                         limit: int = 100,
                         skip: int = 0) -> List[Dict[str, Any]]:
        """Search news with various filters"""
        
        # Build filter criteria
        filter_criteria = {}
        
        if query:
            filter_criteria["$text"] = {"$search": query}
        
        if source:
            filter_criteria["source"] = source
        
        if category:
            filter_criteria["category"] = category
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            filter_criteria["published_date"] = date_filter
        
        if lat_min is not None or lat_max is not None or lng_min is not None or lng_max is not None:
            geo_filter = {}
            if lat_min is not None or lat_max is not None:
                lat_filter = {}
                if lat_min is not None:
                    lat_filter["$gte"] = lat_min
                if lat_max is not None:
                    lat_filter["$lte"] = lat_max
                geo_filter["lat"] = lat_filter
            
            if lng_min is not None or lng_max is not None:
                lng_filter = {}
                if lng_min is not None:
                    lng_filter["$gte"] = lng_min
                if lng_max is not None:
                    lng_filter["$lte"] = lng_max
                geo_filter["lng"] = lng_filter
            
            filter_criteria.update(geo_filter)
        
        # Execute query
        cursor = self.unique_collection.find(filter_criteria)
        
        # Sort by relevance if text search, otherwise by date
        if query:
            cursor = cursor.sort([("score", {"$meta": "textScore"}), ("published_date", DESCENDING)])
        else:
            cursor = cursor.sort("published_date", DESCENDING)
        
        cursor = cursor.skip(skip).limit(limit)
        
        return await cursor.to_list(None)
    
    async def get_news_in_radius(self, center_lat: float, center_lng: float, radius_km: float, limit: int = 100) -> List[Dict[str, Any]]:
        """Get news items within a certain radius of a point"""
        # Convert radius from km to degrees (approximate)
        radius_degrees = radius_km / 111.0  # 1 degree ≈ 111 km
        
        filter_criteria = {
            "lat": {
                "$gte": center_lat - radius_degrees,
                "$lte": center_lat + radius_degrees
            },
            "lng": {
                "$gte": center_lng - radius_degrees,
                "$lte": center_lng + radius_degrees
            }
        }
        
        cursor = self.unique_collection.find(filter_criteria).sort("published_date", DESCENDING).limit(limit)
        return await cursor.to_list(None)
    
    async def get_news_by_location_bounds(self, 
                                        north: float, 
                                        south: float, 
                                        east: float, 
                                        west: float, 
                                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get news items within geographic bounds"""
        filter_criteria = {
            "lat": {"$gte": south, "$lte": north},
            "lng": {"$gte": west, "$lte": east}
        }
        
        cursor = self.unique_collection.find(filter_criteria).sort("published_date", DESCENDING).limit(limit)
        return await cursor.to_list(None)
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        raw_count = await self.get_raw_news_count()
        unique_count = await self.get_unique_news_count()
        source_stats = await self.get_source_stats()
        category_stats = await self.get_category_stats()
        
        # Get date range
        oldest_cursor = self.unique_collection.find().sort("published_date", ASCENDING).limit(1)
        newest_cursor = self.unique_collection.find().sort("published_date", DESCENDING).limit(1)
        
        oldest_docs = await oldest_cursor.to_list(1)
        newest_docs = await newest_cursor.to_list(1)
        
        oldest_date = oldest_docs[0]["published_date"] if oldest_docs else None
        newest_date = newest_docs[0]["published_date"] if newest_docs else None
        
        # Get geolocation stats
        geo_count = await self.unique_collection.count_documents({
            "lat": {"$ne": None}, 
            "lng": {"$ne": None}
        })
        
        return {
            "raw_news_count": raw_count,
            "unique_news_count": unique_count,
            "geolocated_news_count": geo_count,
            "source_distribution": source_stats,
            "category_distribution": category_stats,
            "date_range": {
                "oldest": oldest_date,
                "newest": newest_date
            },
            "last_updated": datetime.utcnow()
        }

# Global database manager instance
db_manager = DatabaseManager()

