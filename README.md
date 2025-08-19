# Bangladesh News Scraper API

A comprehensive FastAPI-based news scraper that collects news from all major Bangladeshi news portals, stores data in MongoDB with geolocation information, and provides advanced filtering endpoints for map visualization.

## Features

- **Multi-Source Scraping**: Scrapes news from 11+ major Bangladeshi news portals
- **Geolocation Integration**: Automatically extracts and geocodes location information using Nominatim/Pelias
- **Intelligent Deduplication**: Advanced content-based deduplication system
- **Advanced Filtering**: Comprehensive API endpoints with geographic, temporal, and text-based filtering
- **Map-Ready Data**: Optimized endpoints for map visualization applications
- **Scalable Architecture**: Asynchronous processing with background tasks
- **Real-time API**: RESTful API with automatic documentation

## Supported News Sources

1. **Prothom Alo** - https://www.prothomalo.com/
2. **The Daily Star** - https://www.thedailystar.net/
3. **bdnews24.com** - https://bdnews24.com/
4. **Jugantor** - https://www.jugantor.com/
5. **Kaler Kantho** - https://www.kalerkantho.com/
6. **Bangladesh Pratidin** - https://www.bd-pratidin.com/
7. **Dhaka Tribune** - https://www.dhakatribune.com/
8. **Daily Nayadiganta** - https://www.dailynayadiganta.com/
9. **The Daily Observer** - https://www.observerbd.com/
10. **BSS** - https://www.bssnews.net/
11. **The Business Standard** - https://www.tbsnews.net/

## Architecture

```
bangladesh_news_scraper/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── api/
│   └── endpoints.py       # API route definitions
├── config/
│   └── settings.py        # Configuration and news source definitions
├── models/
│   └── database.py        # MongoDB models and database operations
├── scrapers/
│   ├── base_scraper.py    # Base scraper class
│   └── scraper_manager.py # Scraper orchestration
├── utils/
│   ├── geolocation.py     # Location extraction and geocoding
│   └── deduplication.py   # Content deduplication logic
├── test_scraper.py        # Test suite
└── run_scraper.py         # CLI tool for scraping operations
```

## Installation

### Prerequisites

- Python 3.11+
- MongoDB 6.0+
- Ubuntu 22.04+ (recommended)

### Setup

1. **Clone or create the project directory:**
```bash
mkdir bangladesh_news_scraper
cd bangladesh_news_scraper
```

2. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
pip3 install aiohttp  # Additional dependency
```

3. **Install and start MongoDB:**
```bash
# Add MongoDB repository
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

4. **Configure environment variables:**
```bash
# Copy and edit .env file
cp .env.example .env
# Edit .env with your preferred settings
```

## Usage

### Starting the API Server

```bash
# Start the FastAPI server
python3 main.py
```

The API will be available at:
- **API Base**: http://localhost:8000/api/v1
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Running News Scraping

#### Command Line Interface

```bash
# Show available news sources
python3 run_scraper.py sources

# Scrape all sources (recommended for first run)
python3 run_scraper.py full

# Scrape a single source
python3 run_scraper.py source daily_star

# Scrape with custom limit
python3 run_scraper.py source prothom_alo 50
```

#### Via API Endpoints

```bash
# Start scraping all sources
curl -X POST "http://localhost:8000/api/v1/scrape"

# Start scraping specific sources
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["daily_star", "prothom_alo"], "limit_per_source": 20}'

# Start deduplication process
curl -X POST "http://localhost:8000/api/v1/deduplicate"
```

### Testing the System

```bash
# Run comprehensive test suite
python3 test_scraper.py

# Run quick demo
python3 test_scraper.py demo
```

## API Endpoints

### Core Endpoints

#### GET /health
Health check endpoint
```bash
curl http://localhost:8000/health
```

#### GET /api/v1/stats
Get comprehensive database statistics
```bash
curl http://localhost:8000/api/v1/stats
```

#### GET /api/v1/sources
Get list of available news sources
```bash
curl http://localhost:8000/api/v1/sources
```

### News Retrieval Endpoints

#### GET /api/v1/news
Advanced news filtering with multiple parameters
```bash
# Basic usage
curl "http://localhost:8000/api/v1/news?limit=10"

# Filter by source
curl "http://localhost:8000/api/v1/news?source=daily_star&limit=5"

# Filter by category
curl "http://localhost:8000/api/v1/news?category=sports&limit=5"

# Text search
curl "http://localhost:8000/api/v1/news?search_text=ঢাকা&limit=5"

# Date range filtering
curl "http://localhost:8000/api/v1/news?date_from=2024-01-01T00:00:00&limit=5"

# Geographic filtering
curl "http://localhost:8000/api/v1/news?lat_min=23.0&lat_max=24.0&lng_min=90.0&lng_max=91.0&limit=5"
```

#### GET /api/v1/news/recent
Get most recent news items
```bash
curl "http://localhost:8000/api/v1/news/recent?limit=10"
```

#### GET /api/v1/news/categories
Get available news categories
```bash
curl "http://localhost:8000/api/v1/news/categories"
```

### Geographic Endpoints

#### GET /api/v1/news/geo/bounds
Get news within geographic bounds
```bash
curl "http://localhost:8000/api/v1/news/geo/bounds?north=24.0&south=23.0&east=91.0&west=90.0&limit=10"
```

#### GET /api/v1/news/geo/radius
Get news within radius of a point
```bash
curl "http://localhost:8000/api/v1/news/geo/radius?lat=23.7&lng=90.4&radius_km=50&limit=10"
```

#### GET /api/v1/news/map-data
Get news data optimized for map visualization
```bash
# All geolocated news
curl "http://localhost:8000/api/v1/news/map-data?limit=100"

# Within specific bounds
curl "http://localhost:8000/api/v1/news/map-data?bounds=24.0,23.0,91.0,90.0&limit=100"
```

### Background Operations

#### POST /api/v1/scrape
Start news scraping process
```bash
# Scrape all sources
curl -X POST "http://localhost:8000/api/v1/scrape"

# Scrape specific sources
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["daily_star", "prothom_alo"], "limit_per_source": 20}'
```

#### POST /api/v1/deduplicate
Start deduplication process
```bash
curl -X POST "http://localhost:8000/api/v1/deduplicate"
```

## Data Schema

### News Item Structure

```json
{
  "_id": "ObjectId",
  "title": "News headline",
  "description": "Full article content or summary",
  "source_url": "Original article URL",
  "image_url": "Featured image URL (optional)",
  "source": "Source name (e.g., 'The Daily Star')",
  "category": "Article category (optional)",
  "lat": 23.7644,
  "lng": 90.3432,
  "published_date": "2024-01-01T12:00:00Z",
  "scraped_date": "2024-01-01T12:30:00Z",
  "tags": ["tag1", "tag2"]
}
```

### Database Collections

1. **raw_news**: All scraped articles before deduplication
2. **unique_news**: Deduplicated articles with enhanced metadata

## Configuration

### Environment Variables (.env)

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bangladesh_news
RAW_COLLECTION=raw_news
UNIQUE_COLLECTION=unique_news

# Geolocation Settings
NOMINATIM_USER_AGENT=bangladesh_news_scraper
PELIAS_API_URL=https://api.geocode.earth/v1

# Scraping Settings
SCRAPING_DELAY=1
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30

# Redis Settings (for Celery)
REDIS_URL=redis://localhost:6379/0
```

### News Source Configuration

Each news source is configured in `config/settings.py` with:
- Base URL and RSS feed URLs
- CSS selectors for content extraction
- Category mapping rules

## Geolocation Features

### Location Extraction

The system automatically extracts location information from news content using:
- Pattern matching for Bangladeshi cities, districts, and areas
- Support for both Bengali and English location names
- Comprehensive database of 200+ Bangladeshi locations

### Geocoding Services

- **Primary**: Nominatim (OpenStreetMap)
- **Fallback**: Pelias API
- **Caching**: In-memory cache for performance
- **Rate Limiting**: Respects service limits

### Supported Locations

Major cities, districts, and areas across Bangladesh including:
- All 64 districts
- Major metropolitan areas
- Popular localities in Dhaka, Chittagong, Sylhet, etc.
- Both Bengali and English names

## Deduplication System

### Content-Based Deduplication

- **URL Matching**: Exact URL duplicate detection
- **Content Hashing**: MD5 hashing of normalized content
- **Similarity Analysis**: Text similarity using SequenceMatcher
- **Smart Merging**: Combines information from similar articles

### Deduplication Process

1. **Raw Collection**: All scraped articles stored initially
2. **Content Analysis**: Extract and normalize text content
3. **Similarity Detection**: Find articles with similar titles/content
4. **Intelligent Merging**: Combine duplicate articles keeping best information
5. **Unique Collection**: Final deduplicated dataset

## Performance Optimization

### Database Indexes

Optimized indexes for common query patterns:
- Text search indexes on title and description
- Geographic indexes for lat/lng queries
- Compound indexes for filtered queries
- Unique indexes for deduplication

### Async Processing

- Asynchronous web scraping with connection pooling
- Background task processing for long-running operations
- Concurrent request handling with rate limiting

### Caching Strategy

- In-memory caching for geolocation results
- Database query optimization
- Efficient batch processing

## Monitoring and Logging

### Logging Configuration

Comprehensive logging for:
- Scraping operations and results
- Database operations
- API requests and responses
- Error tracking and debugging

### Statistics and Monitoring

Real-time statistics available via API:
- Total articles scraped
- Source distribution
- Geographic coverage
- Processing performance metrics

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```bash
   # Check MongoDB status
   sudo systemctl status mongod
   
   # Restart if needed
   sudo systemctl restart mongod
   ```

2. **Scraping Errors**
   ```bash
   # Check individual source
   python3 run_scraper.py source daily_star 5
   
   # View detailed logs
   python3 test_scraper.py
   ```

3. **Geolocation Issues**
   ```bash
   # Test geolocation service
   python3 -c "
   import asyncio
   from utils.geolocation import GeolocationService
   
   async def test():
       async with GeolocationService() as geo:
           result = await geo.geocode_location('Dhaka')
           print(result)
   
   asyncio.run(test())
   "
   ```

### Performance Tuning

1. **Increase Scraping Concurrency**
   - Edit `MAX_CONCURRENT_REQUESTS` in `.env`
   - Monitor system resources

2. **Database Optimization**
   - Ensure proper indexing
   - Regular cleanup of old data
   - Monitor query performance

3. **Memory Management**
   - Adjust batch sizes for large datasets
   - Monitor memory usage during processing

## Development

### Adding New News Sources

1. Add source configuration to `config/settings.py`
2. Test with single source scraping
3. Update documentation

### Extending API Endpoints

1. Add new endpoints to `api/endpoints.py`
2. Update database models if needed
3. Add tests and documentation

### Custom Geolocation Patterns

1. Edit location patterns in `utils/geolocation.py`
2. Test with sample news content
3. Update location database

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review the test suite output
3. Examine application logs
4. Create detailed issue reports

## Changelog

### Version 1.0.0
- Initial release with full scraping functionality
- 11 news sources supported
- Advanced geolocation integration
- Comprehensive API endpoints
- Intelligent deduplication system
- Map-ready data endpoints

# scraper
