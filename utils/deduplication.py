import asyncio
import hashlib
import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime
import re
from difflib import SequenceMatcher
from motor.motor_asyncio import AsyncIOMotorCollection
from models.database import db_manager
from utils.geolocation import GeolocationService

logger = logging.getLogger(__name__)

class NewsDeduplicator:
    def __init__(self):
        self.similarity_threshold = 0.85  # Threshold for considering articles similar
        self.title_similarity_threshold = 0.90  # Higher threshold for titles
        self.processed_urls: Set[str] = set()
        self.processed_hashes: Set[str] = set()
        self.geolocation_service = GeolocationService()
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s\u0980-\u09FF]', '', text)
        
        # Remove common stop words (both English and Bengali)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'এ', 'এই', 'ও', 'এবং', 'কিন্তু', 'তবে', 'যে', 'যা', 'যার', 'যাকে', 'যাদের', 'সে', 'তার', 'তাকে', 'তাদের'
        }
        
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        normalized_text1 = self.normalize_text(text1)
        normalized_text2 = self.normalize_text(text2)
        
        if not normalized_text1 or not normalized_text2:
            return 0.0
        
        return SequenceMatcher(None, normalized_text1, normalized_text2).ratio()
    
    def generate_content_hash(self, article: Dict[str, Any]) -> str:
        """Generate a hash for article content"""
        # Combine normalized title and description
        title = self.normalize_text(article.get('title', ''))
        description = self.normalize_text(article.get('description', ''))
        
        content = f"{title}|{description}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def is_duplicate_by_url(self, article: Dict[str, Any]) -> bool:
        """Check if article is duplicate based on URL"""
        url = article.get('source_url', '')
        if url in self.processed_urls:
            return True
        return False
    
    def is_duplicate_by_content(self, article: Dict[str, Any]) -> bool:
        """Check if article is duplicate based on content hash"""
        content_hash = self.generate_content_hash(article)
        if content_hash in self.processed_hashes:
            return True
        return False
    
    async def find_similar_articles(self, article: Dict[str, Any], collection: AsyncIOMotorCollection) -> List[Dict[str, Any]]:
        """Find similar articles in the database"""
        title = article.get('title', '')
        if not title:
            return []
        
        # Search for articles with similar titles using text search
        similar_articles = []
        
        try:
            # First, try exact URL match
            exact_match = await collection.find_one({"source_url": article.get('source_url', '')})
            if exact_match:
                return [exact_match]
            
            # Then search by title similarity using text search
            cursor = collection.find(
                {"$text": {"$search": title}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(10)
            
            candidates = await cursor.to_list(None)
            
            # Calculate similarity for each candidate
            for candidate in candidates:
                title_similarity = self.calculate_text_similarity(
                    article.get('title', ''), 
                    candidate.get('title', '')
                )
                
                description_similarity = self.calculate_text_similarity(
                    article.get('description', ''), 
                    candidate.get('description', '')
                )
                
                # Consider it similar if title similarity is high or both title and description are moderately similar
                if (title_similarity >= self.title_similarity_threshold or 
                    (title_similarity >= 0.7 and description_similarity >= 0.7)):
                    similar_articles.append(candidate)
            
            return similar_articles
            
        except Exception as e:
            logger.error(f"Error finding similar articles: {str(e)}")
            return []
    
    def merge_articles(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two similar articles, keeping the best information"""
        merged = existing.copy()
        
        # Keep the more recent scraped date
        if new.get('scraped_date', datetime.min) > existing.get('scraped_date', datetime.min):
            merged['scraped_date'] = new['scraped_date']
        
        # Keep the earlier published date if available
        new_pub_date = new.get('published_date')
        existing_pub_date = existing.get('published_date')
        
        if new_pub_date and existing_pub_date:
            merged['published_date'] = min(new_pub_date, existing_pub_date)
        elif new_pub_date:
            merged['published_date'] = new_pub_date
        
        # Keep the longer description
        new_desc = new.get('description', '')
        existing_desc = existing.get('description', '')
        
        if len(new_desc) > len(existing_desc):
            merged['description'] = new_desc
        
        # Keep image URL if new one is available and existing doesn't have one
        if new.get('image_url') and not existing.get('image_url'):
            merged['image_url'] = new['image_url']
        
        # Keep geolocation if new one is available and existing doesn't have one
        if new.get('lat') and new.get('lng') and (not existing.get('lat') or not existing.get('lng')):
            merged['lat'] = new['lat']
            merged['lng'] = new['lng']
        
        # Merge tags
        existing_tags = set(existing.get('tags', []))
        new_tags = set(new.get('tags', []))
        merged['tags'] = list(existing_tags.union(new_tags))
        
        # Keep category if new one is available and existing doesn't have one
        if new.get('category') and not existing.get('category'):
            merged['category'] = new['category']
        
        return merged
    
    async def process_raw_to_unique(self, batch_size: int = 100) -> Dict[str, Any]:
        """Process raw news collection to create unique collection"""
        logger.info("Starting deduplication process")
        
        stats = {
            'processed': 0,
            'duplicates_found': 0,
            'unique_added': 0,
            'updated': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
        
        try:
            # Get raw collection cursor
            raw_collection = db_manager.raw_collection
            unique_collection = db_manager.unique_collection
            
            # Process in batches
            cursor = raw_collection.find().batch_size(batch_size)
            
            async with self.geolocation_service:
                async for raw_article in cursor:
                    try:
                        stats['processed'] += 1
                        
                        # Skip if already processed by URL
                        if self.is_duplicate_by_url(raw_article):
                            stats['duplicates_found'] += 1
                            continue
                        
                        # Skip if already processed by content hash
                        if self.is_duplicate_by_content(raw_article):
                            stats['duplicates_found'] += 1
                            continue
                        
                        # Find similar articles in unique collection
                        similar_articles = await self.find_similar_articles(raw_article, unique_collection)
                        
                        if similar_articles:
                            # Update existing article with merged information
                            existing_article = similar_articles[0]
                            merged_article = self.merge_articles(existing_article, raw_article)
                            
                            await unique_collection.replace_one(
                                {"_id": existing_article["_id"]}, 
                                merged_article
                            )
                            
                            stats['updated'] += 1
                            stats['duplicates_found'] += 1
                        else:
                            # Add geolocation if not present
                            if not raw_article.get('lat') or not raw_article.get('lng'):
                                lat_lng = await self.geolocation_service.get_location_for_news(raw_article)
                                if lat_lng:
                                    raw_article['lat'], raw_article['lng'] = lat_lng
                            
                            # Insert as new unique article
                            try:
                                await unique_collection.insert_one(raw_article)
                                stats['unique_added'] += 1
                            except Exception as e:
                                if "duplicate key error" in str(e).lower():
                                    stats['duplicates_found'] += 1
                                else:
                                    raise e
                        
                        # Update processed sets
                        self.processed_urls.add(raw_article.get('source_url', ''))
                        self.processed_hashes.add(self.generate_content_hash(raw_article))
                        
                        # Log progress
                        if stats['processed'] % 100 == 0:
                            logger.info(f"Processed {stats['processed']} articles, "
                                      f"added {stats['unique_added']} unique, "
                                      f"found {stats['duplicates_found']} duplicates")
                    
                    except Exception as e:
                        logger.error(f"Error processing article: {str(e)}")
                        stats['errors'] += 1
                        continue
        
        except Exception as e:
            logger.error(f"Error in deduplication process: {str(e)}")
            stats['errors'] += 1
        
        stats['end_time'] = datetime.utcnow()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        logger.info(f"Deduplication completed. Processed: {stats['processed']}, "
                   f"Unique added: {stats['unique_added']}, "
                   f"Duplicates found: {stats['duplicates_found']}, "
                   f"Updated: {stats['updated']}, "
                   f"Errors: {stats['errors']}")
        
        return stats
    
    async def cleanup_duplicates_in_unique_collection(self) -> Dict[str, Any]:
        """Clean up any remaining duplicates in the unique collection"""
        logger.info("Starting cleanup of duplicates in unique collection")
        
        stats = {
            'checked': 0,
            'duplicates_removed': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
        
        try:
            unique_collection = db_manager.unique_collection
            
            # Find articles with duplicate URLs
            pipeline = [
                {"$group": {
                    "_id": "$source_url",
                    "count": {"$sum": 1},
                    "docs": {"$push": "$$ROOT"}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            
            cursor = unique_collection.aggregate(pipeline)
            
            async for group in cursor:
                try:
                    docs = group['docs']
                    stats['checked'] += len(docs)
                    
                    # Keep the most recent one, remove others
                    docs.sort(key=lambda x: x.get('scraped_date', datetime.min), reverse=True)
                    keep_doc = docs[0]
                    remove_docs = docs[1:]
                    
                    # Merge information from all duplicates into the one we're keeping
                    for doc in remove_docs:
                        keep_doc = self.merge_articles(keep_doc, doc)
                    
                    # Update the document we're keeping
                    await unique_collection.replace_one(
                        {"_id": keep_doc["_id"]}, 
                        keep_doc
                    )
                    
                    # Remove the duplicates
                    for doc in remove_docs:
                        await unique_collection.delete_one({"_id": doc["_id"]})
                        stats['duplicates_removed'] += 1
                
                except Exception as e:
                    logger.error(f"Error cleaning up duplicate group: {str(e)}")
                    stats['errors'] += 1
                    continue
        
        except Exception as e:
            logger.error(f"Error in cleanup process: {str(e)}")
            stats['errors'] += 1
        
        stats['end_time'] = datetime.utcnow()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        logger.info(f"Cleanup completed. Checked: {stats['checked']}, "
                   f"Duplicates removed: {stats['duplicates_removed']}, "
                   f"Errors: {stats['errors']}")
        
        return stats

# Global deduplicator instance
deduplicator = NewsDeduplicator()

