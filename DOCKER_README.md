# Docker Deployment Guide

This guide explains how to run the Bangladesh News Scraper application using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.0 or higher)
- Docker Compose (version 2.0 or higher)

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd bangladesh_news_scraper
   ```

2. **Build and start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Main API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555
   - MongoDB: localhost:27017
   - Redis: localhost:6379

## Services

The Docker Compose setup includes the following services:

### 1. Main Application (`app`)
- **Port**: 8000
- **Description**: FastAPI application serving the REST API
- **Health Check**: Available at `/health` endpoint

### 2. MongoDB (`mongodb`)
- **Port**: 27017
- **Description**: MongoDB database for storing news data
- **Credentials**: 
  - Username: `admin`
  - Password: `password123`
  - Database: `bangladesh_news`

### 3. Redis (`redis`)
- **Port**: 6379
- **Description**: Redis server for Celery task queue

### 4. Celery Worker (`celery_worker`)
- **Description**: Background worker for processing scraping tasks

### 5. Celery Beat (`celery_beat`)
- **Description**: Scheduler for periodic scraping tasks

### 6. Flower (`flower`)
- **Port**: 5555
- **Description**: Web-based monitoring tool for Celery

## Commands

### Start all services
```bash
docker-compose up
```

### Start in background (detached mode)
```bash
docker-compose up -d
```

### Build and start
```bash
docker-compose up --build
```

### Stop all services
```bash
docker-compose down
```

### Stop and remove volumes (WARNING: This will delete all data)
```bash
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs mongodb
docker-compose logs celery_worker
```

### Restart a specific service
```bash
docker-compose restart app
```

### Scale services
```bash
# Run multiple worker instances
docker-compose up --scale celery_worker=3
```

## Environment Variables

The application uses the following environment variables in Docker:

- `MONGODB_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name (default: bangladesh_news)
- `RAW_COLLECTION`: Raw news collection name
- `UNIQUE_COLLECTION`: Unique news collection name
- `REDIS_URL`: Redis connection string
- `SCRAPING_DELAY`: Delay between requests
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent requests
- `REQUEST_TIMEOUT`: Request timeout in seconds

## Data Persistence

- **MongoDB data**: Stored in `mongodb_data` Docker volume
- **Redis data**: Stored in `redis_data` Docker volume
- **Application logs**: Mounted to `./logs` directory on host

## Development

### Running individual services

```bash
# Start only database services
docker-compose up mongodb redis

# Start app with live reload (for development)
docker-compose up app
```

### Accessing containers

```bash
# Access app container
docker-compose exec app bash

# Access MongoDB container
docker-compose exec mongodb mongo -u admin -p password123

# Access Redis container
docker-compose exec redis redis-cli
```

### Database Management

```bash
# Access MongoDB shell
docker-compose exec mongodb mongo bangladesh_news -u admin -p password123

# Import/Export data
docker-compose exec mongodb mongodump --uri="mongodb://admin:password123@localhost:27017/bangladesh_news"
```

## Troubleshooting

### Check service status
```bash
docker-compose ps
```

### Check logs for errors
```bash
docker-compose logs app
docker-compose logs mongodb
```

### Restart problematic services
```bash
docker-compose restart app
docker-compose restart mongodb
```

### Clean rebuild
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Common Issues

1. **Port already in use**: Change port mappings in `docker-compose.yml`
2. **Permission issues**: Ensure Docker has necessary permissions
3. **MongoDB connection issues**: Check if MongoDB service is running and accessible
4. **Celery worker not starting**: Check Redis connection and worker logs

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use `.env` file or external secrets management
2. **Security**: Change default passwords and use strong credentials
3. **Monitoring**: Set up proper logging and monitoring
4. **Backup**: Implement regular database backups
5. **SSL/TLS**: Configure HTTPS for API endpoints
6. **Resource Limits**: Set appropriate resource limits in Docker Compose

### Example production `.env` file:
```env
MONGODB_URL=mongodb://your_user:your_password@mongodb:27017/bangladesh_news?authSource=admin
REDIS_URL=redis://redis:6379/0
SCRAPING_DELAY=2
MAX_CONCURRENT_REQUESTS=3
```

## API Usage

Once the application is running, you can:

1. **View API documentation**: http://localhost:8000/docs
2. **Check health**: http://localhost:8000/health
3. **Access API endpoints**: http://localhost:8000/api/v1/

### Example API calls:
```bash
# Health check
curl http://localhost:8000/health

# Get unique news
curl http://localhost:8000/api/v1/news/unique

# Start scraping
curl -X POST http://localhost:8000/api/v1/scrape/start
```
