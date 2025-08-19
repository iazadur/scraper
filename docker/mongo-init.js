// MongoDB initialization script
db = db.getSiblingDB('bangladesh_news');

// Create collections
db.createCollection('raw_news');
db.createCollection('unique_news');

// Create indexes for better performance
db.raw_news.createIndex({ "url": 1 }, { unique: true });
db.raw_news.createIndex({ "source": 1 });
db.raw_news.createIndex({ "published_date": -1 });
db.raw_news.createIndex({ "scraped_at": -1 });

db.unique_news.createIndex({ "content_hash": 1 }, { unique: true });
db.unique_news.createIndex({ "source": 1 });
db.unique_news.createIndex({ "published_date": -1 });
db.unique_news.createIndex({ "location.coordinates": "2dsphere" });
db.unique_news.createIndex({ "category": 1 });

print('Database initialization completed successfully!');
