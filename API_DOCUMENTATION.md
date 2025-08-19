# API Documentation

Complete API reference for the Bangladesh News Scraper API.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. For production deployment, consider implementing API key authentication or OAuth2.

## Response Format

All API responses follow this standard format:

```json
{
  "success": true,
  "count": 10,
  "data": [...],
  "message": "Optional message",
  "filters": {...},
  "error": "Error message (only on failure)"
}
```

## Error Handling

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error Response Example:
```json
{
  "success": false,
  "error": "Invalid parameter: source must be one of [daily_star, prothom_alo, ...]",
  "detail": "Validation failed"
}
```

## Endpoints

### System Endpoints

#### GET /health
Health check endpoint to verify API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "stats": {
    "unique_news_count": 1250,
    "raw_news_count": 1500,
    "geolocated_news_count": 1100
  }
}
```

#### GET /api/v1/stats
Get comprehensive database statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "raw_news_count": 1500,
    "unique_news_count": 1250,
    "geolocated_news_count": 1100,
    "source_distribution": [
      {"source": "The Daily Star", "count": 200},
      {"source": "Prothom Alo", "count": 180}
    ],
    "category_distribution": [
      {"category": "national", "count": 300},
      {"category": "international", "count": 250}
    ],
    "date_range": {
      "oldest": "2024-01-01T00:00:00Z",
      "newest": "2024-01-15T12:00:00Z"
    },
    "last_updated": "2024-01-15T12:30:00Z"
  }
}
```

#### GET /api/v1/sources
Get list of available news sources.

**Response:**
```json
{
  "success": true,
  "count": 11,
  "data": [
    {
      "key": "daily_star",
      "name": "The Daily Star",
      "base_url": "https://www.thedailystar.net",
      "rss_feeds_count": 4
    },
    {
      "key": "prothom_alo",
      "name": "Prothom Alo",
      "base_url": "https://www.prothomalo.com",
      "rss_feeds_count": 5
    }
  ]
}
```

### News Retrieval Endpoints

#### GET /api/v1/news
Advanced news filtering with multiple parameters.

**Parameters:**
- `source` (string, optional): Filter by news source key
- `category` (string, optional): Filter by category
- `search_text` (string, optional): Search in title and description
- `date_from` (datetime, optional): Filter news from this date (ISO format)
- `date_to` (datetime, optional): Filter news until this date (ISO format)
- `lat_min` (float, optional): Minimum latitude for geographic filter
- `lat_max` (float, optional): Maximum latitude for geographic filter
- `lng_min` (float, optional): Minimum longitude for geographic filter
- `lng_max` (float, optional): Maximum longitude for geographic filter
- `limit` (integer, optional): Maximum number of results (1-1000, default: 100)
- `skip` (integer, optional): Number of results to skip (default: 0)

**Example Requests:**

```bash
# Basic usage
GET /api/v1/news?limit=10

# Filter by source
GET /api/v1/news?source=daily_star&limit=5

# Filter by category
GET /api/v1/news?category=sports&limit=5

# Text search
GET /api/v1/news?search_text=ঢাকা&limit=5

# Date range filtering
GET /api/v1/news?date_from=2024-01-01T00:00:00&date_to=2024-01-15T23:59:59&limit=10

# Geographic filtering (Dhaka area)
GET /api/v1/news?lat_min=23.7&lat_max=23.8&lng_min=90.3&lng_max=90.5&limit=10

# Combined filters
GET /api/v1/news?source=daily_star&category=national&search_text=government&limit=5
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "_id": "65a1b2c3d4e5f6789012345",
      "title": "Major development project announced in Dhaka",
      "description": "The government has announced a new infrastructure development project...",
      "source_url": "https://www.thedailystar.net/news/article-123456",
      "image_url": "https://www.thedailystar.net/images/article-123456.jpg",
      "source": "The Daily Star",
      "category": "national",
      "lat": 23.7644,
      "lng": 90.3432,
      "published_date": "2024-01-15T10:30:00Z",
      "scraped_date": "2024-01-15T11:00:00Z",
      "tags": ["development", "infrastructure", "dhaka"]
    }
  ],
  "filters": {
    "source": "daily_star",
    "category": null,
    "search_text": null,
    "date_from": null,
    "date_to": null,
    "geographic_bounds": {
      "lat_min": null,
      "lat_max": null,
      "lng_min": null,
      "lng_max": null
    },
    "limit": 5,
    "skip": 0
  }
}
```

#### GET /api/v1/news/recent
Get most recent news items.

**Parameters:**
- `limit` (integer, optional): Number of recent news items (1-500, default: 50)

**Example Request:**
```bash
GET /api/v1/news/recent?limit=10
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "_id": "65a1b2c3d4e5f6789012345",
      "title": "Latest breaking news headline",
      "description": "Breaking news content...",
      "source_url": "https://example.com/news/123",
      "source": "The Daily Star",
      "published_date": "2024-01-15T12:00:00Z",
      "lat": 23.7644,
      "lng": 90.3432
    }
  ]
}
```

#### GET /api/v1/news/categories
Get available news categories with statistics.

**Response:**
```json
{
  "success": true,
  "count": 8,
  "data": [
    "national",
    "international", 
    "sports",
    "business",
    "entertainment",
    "technology",
    "politics",
    "opinion"
  ],
  "stats": [
    {"category": "national", "count": 300},
    {"category": "international", "count": 250},
    {"category": "sports", "count": 180},
    {"category": "business", "count": 150}
  ]
}
```

### Geographic Endpoints

#### GET /api/v1/news/geo/bounds
Get news within specific geographic bounds.

**Parameters:**
- `north` (float, required): Northern boundary latitude
- `south` (float, required): Southern boundary latitude  
- `east` (float, required): Eastern boundary longitude
- `west` (float, required): Western boundary longitude
- `limit` (integer, optional): Maximum number of results (1-1000, default: 100)

**Example Request:**
```bash
# Get news within Dhaka metropolitan area
GET /api/v1/news/geo/bounds?north=23.9&south=23.6&east=90.6&west=90.2&limit=20
```

**Response:**
```json
{
  "success": true,
  "count": 15,
  "data": [
    {
      "_id": "65a1b2c3d4e5f6789012345",
      "title": "Local news from Dhaka",
      "lat": 23.7644,
      "lng": 90.3432,
      "source": "Prothom Alo"
    }
  ],
  "bounds": {
    "north": 23.9,
    "south": 23.6,
    "east": 90.6,
    "west": 90.2
  }
}
```

#### GET /api/v1/news/geo/radius
Get news within a radius of a specific point.

**Parameters:**
- `lat` (float, required): Center latitude
- `lng` (float, required): Center longitude
- `radius_km` (float, required): Radius in kilometers
- `limit` (integer, optional): Maximum number of results (1-1000, default: 100)

**Example Request:**
```bash
# Get news within 50km of Dhaka center
GET /api/v1/news/geo/radius?lat=23.7644&lng=90.3432&radius_km=50&limit=25
```

**Response:**
```json
{
  "success": true,
  "count": 20,
  "data": [
    {
      "_id": "65a1b2c3d4e5f6789012345",
      "title": "News near Dhaka",
      "lat": 23.8103,
      "lng": 90.4125,
      "source": "bdnews24.com"
    }
  ],
  "center": {
    "lat": 23.7644,
    "lng": 90.3432
  },
  "radius_km": 50
}
```

#### GET /api/v1/news/map-data
Get news data optimized for map visualization.

**Parameters:**
- `bounds` (string, optional): Geographic bounds as 'north,south,east,west'
- `limit` (integer, optional): Maximum number of results (1-5000, default: 1000)

**Example Requests:**
```bash
# Get all geolocated news for map
GET /api/v1/news/map-data?limit=500

# Get news within specific bounds
GET /api/v1/news/map-data?bounds=24.0,23.0,91.0,90.0&limit=200
```

**Response:**
```json
{
  "success": true,
  "count": 150,
  "data": [
    {
      "id": "65a1b2c3d4e5f6789012345",
      "title": "News headline for map display",
      "description": "Truncated description for map popup...",
      "source": "The Daily Star",
      "category": "national",
      "lat": 23.7644,
      "lng": 90.3432,
      "published_date": "2024-01-15T10:30:00Z",
      "source_url": "https://example.com/news/123",
      "image_url": "https://example.com/image.jpg"
    }
  ],
  "bounds": "24.0,23.0,91.0,90.0"
}
```

### Background Operations

#### POST /api/v1/scrape
Start news scraping process in the background.

**Request Body (JSON):**
```json
{
  "sources": ["daily_star", "prothom_alo"],  // Optional: specific sources
  "limit_per_source": 20                     // Optional: limit per source
}
```

**Example Requests:**

```bash
# Scrape all sources
POST /api/v1/scrape
Content-Type: application/json
{}

# Scrape specific sources
POST /api/v1/scrape
Content-Type: application/json
{
  "sources": ["daily_star", "prothom_alo"],
  "limit_per_source": 50
}
```

**Response:**
```json
{
  "success": true,
  "message": "Started scraping 2 sources",
  "sources": ["daily_star", "prothom_alo"]
}
```

#### POST /api/v1/deduplicate
Start deduplication process in the background.

**Example Request:**
```bash
POST /api/v1/deduplicate
```

**Response:**
```json
{
  "success": true,
  "message": "Started deduplication process"
}
```

## Data Models

### News Item Schema

```json
{
  "_id": "ObjectId",                    // MongoDB ObjectId
  "title": "string",                    // News headline
  "description": "string",              // Full article content or summary
  "source_url": "string",               // Original article URL (unique)
  "image_url": "string|null",           // Featured image URL
  "source": "string",                   // Source name (e.g., "The Daily Star")
  "category": "string|null",            // Article category
  "lat": "number|null",                 // Latitude coordinate
  "lng": "number|null",                 // Longitude coordinate
  "published_date": "datetime|null",    // Original publication date
  "scraped_date": "datetime",           // When article was scraped
  "tags": ["string"]                    // Article tags/keywords
}
```

### Filter Parameters Schema

```json
{
  "source": "string|null",              // Source filter
  "category": "string|null",            // Category filter
  "search_text": "string|null",        // Text search query
  "date_from": "datetime|null",         // Start date filter
  "date_to": "datetime|null",           // End date filter
  "lat_min": "number|null",             // Geographic bounds
  "lat_max": "number|null",
  "lng_min": "number|null", 
  "lng_max": "number|null",
  "limit": "integer",                   // Result limit (1-1000)
  "skip": "integer"                     // Results to skip (pagination)
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider implementing:

- Per-IP rate limiting (e.g., 1000 requests/hour)
- API key-based rate limiting
- Different limits for different endpoint types

## Pagination

Use `limit` and `skip` parameters for pagination:

```bash
# Page 1 (first 20 items)
GET /api/v1/news?limit=20&skip=0

# Page 2 (next 20 items)  
GET /api/v1/news?limit=20&skip=20

# Page 3 (next 20 items)
GET /api/v1/news?limit=20&skip=40
```

## Sorting

Results are automatically sorted by:
- **Text search queries**: Relevance score, then publication date (descending)
- **Other queries**: Publication date (descending)

## Geographic Coordinate System

All geographic coordinates use the WGS84 coordinate system:
- **Latitude**: -90 to +90 degrees
- **Longitude**: -180 to +180 degrees
- **Bangladesh bounds**: Approximately lat 20.5-26.5, lng 88.0-92.7

## Supported News Sources

| Key | Name | Language | RSS Feeds |
|-----|------|----------|-----------|
| `daily_star` | The Daily Star | English | 4 |
| `prothom_alo` | Prothom Alo | Bengali | 5 |
| `bdnews24` | bdnews24.com | Bengali/English | 4 |
| `jugantor` | Jugantor | Bengali | 4 |
| `kaler_kantho` | Kaler Kantho | Bengali | 4 |
| `bangladesh_pratidin` | Bangladesh Pratidin | Bengali | 4 |
| `dhaka_tribune` | Dhaka Tribune | English | 4 |
| `daily_nayadiganta` | Daily Nayadiganta | Bengali | 4 |
| `daily_observer` | The Daily Observer | English | 4 |
| `bss` | BSS | Bengali/English | 4 |
| `business_standard` | The Business Standard | English | 4 |

## Common Use Cases

### 1. Building a News Map Application

```javascript
// Fetch map data
const response = await fetch('/api/v1/news/map-data?limit=1000');
const data = await response.json();

// Use data.data array to populate map markers
data.data.forEach(news => {
  addMapMarker(news.lat, news.lng, {
    title: news.title,
    description: news.description,
    source: news.source,
    url: news.source_url
  });
});
```

### 2. Creating a News Dashboard

```javascript
// Get recent news
const recent = await fetch('/api/v1/news/recent?limit=10');

// Get statistics
const stats = await fetch('/api/v1/stats');

// Get news by category
const sports = await fetch('/api/v1/news?category=sports&limit=5');
const business = await fetch('/api/v1/news?category=business&limit=5');
```

### 3. Location-Based News Feed

```javascript
// Get user's location
navigator.geolocation.getCurrentPosition(async (position) => {
  const lat = position.coords.latitude;
  const lng = position.coords.longitude;
  
  // Get nearby news (within 100km)
  const nearby = await fetch(
    `/api/v1/news/geo/radius?lat=${lat}&lng=${lng}&radius_km=100&limit=20`
  );
});
```

### 4. Search and Filter Interface

```javascript
// Build search query
const params = new URLSearchParams();
if (searchText) params.append('search_text', searchText);
if (selectedSource) params.append('source', selectedSource);
if (selectedCategory) params.append('category', selectedCategory);
if (dateFrom) params.append('date_from', dateFrom);
if (dateTo) params.append('date_to', dateTo);
params.append('limit', '20');

const results = await fetch(`/api/v1/news?${params}`);
```

## WebSocket Support

Currently not implemented. For real-time updates, consider polling the `/api/v1/news/recent` endpoint or implementing WebSocket support for live news feeds.

## API Versioning

The current API version is `v1`. Future versions will be available at:
- `/api/v2/...` (when available)
- Backward compatibility maintained for at least one major version

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive testing capabilities and detailed schema information.

