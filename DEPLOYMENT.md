# Deployment Guide

This guide covers deploying the Bangladesh News Scraper API to production environments.

## Production Deployment Options

### Option 1: Traditional Server Deployment

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.11+
- MongoDB 6.0+
- Nginx (recommended)
- SSL certificate

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-pip python3.11-venv nginx

# Create application user
sudo useradd -m -s /bin/bash newscraper
sudo usermod -aG sudo newscraper
```

#### Step 2: MongoDB Installation

```bash
# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# Configure MongoDB for production
sudo nano /etc/mongod.conf
# Enable authentication and configure bind IP

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database user
mongosh
use bangladesh_news
db.createUser({
  user: "newscraper",
  pwd: "your_secure_password",
  roles: [{ role: "readWrite", db: "bangladesh_news" }]
})
```

#### Step 3: Application Deployment

```bash
# Switch to application user
sudo su - newscraper

# Clone/upload application
git clone <your-repo> /home/newscraper/bangladesh_news_scraper
cd /home/newscraper/bangladesh_news_scraper

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install aiohttp gunicorn

# Configure environment
cp .env.example .env
nano .env
# Update MongoDB URL with authentication:
# MONGODB_URL=mongodb://newscraper:your_secure_password@localhost:27017/bangladesh_news
```

#### Step 4: Systemd Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/bangladesh-news-api.service
```

```ini
[Unit]
Description=Bangladesh News Scraper API
After=network.target mongodb.service

[Service]
Type=exec
User=newscraper
Group=newscraper
WorkingDirectory=/home/newscraper/bangladesh_news_scraper
Environment=PATH=/home/newscraper/bangladesh_news_scraper/venv/bin
ExecStart=/home/newscraper/bangladesh_news_scraper/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bangladesh-news-api
sudo systemctl start bangladesh-news-api
sudo systemctl status bangladesh-news-api
```

#### Step 5: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/bangladesh-news-api
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optional: Serve static files directly
    location /static/ {
        alias /home/newscraper/bangladesh_news_scraper/static/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/bangladesh-news-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir aiohttp gunicorn

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 newscraper && chown -R newscraper:newscraper /app
USER newscraper

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: bangladesh-news-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: your_admin_password
      MONGO_INITDB_DATABASE: bangladesh_news
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    ports:
      - "27017:27017"
    networks:
      - bangladesh-news-network

  api:
    build: .
    container_name: bangladesh-news-api
    restart: unless-stopped
    environment:
      MONGODB_URL: mongodb://newscraper:your_secure_password@mongodb:27017/bangladesh_news
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
    networks:
      - bangladesh-news-network
    volumes:
      - ./logs:/app/logs

  nginx:
    image: nginx:alpine
    container_name: bangladesh-news-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - bangladesh-news-network

volumes:
  mongodb_data:

networks:
  bangladesh-news-network:
    driver: bridge
```

#### MongoDB Initialization Script

```javascript
// mongo-init.js
db = db.getSiblingDB('bangladesh_news');

db.createUser({
  user: 'newscraper',
  pwd: 'your_secure_password',
  roles: [
    {
      role: 'readWrite',
      db: 'bangladesh_news'
    }
  ]
});

// Create collections and indexes
db.createCollection('raw_news');
db.createCollection('unique_news');

// Create indexes
db.unique_news.createIndex({ "source_url": 1 }, { unique: true });
db.unique_news.createIndex({ "title": "text", "description": "text" });
db.unique_news.createIndex({ "lat": 1, "lng": 1 });
db.unique_news.createIndex({ "source": 1 });
db.unique_news.createIndex({ "published_date": -1 });
db.unique_news.createIndex({ "category": 1 });
```

### Option 3: Cloud Deployment (AWS/GCP/Azure)

#### AWS Deployment with ECS

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name bangladesh-news-scraper
```

2. **Build and Push Docker Image**
```bash
# Build image
docker build -t bangladesh-news-scraper .

# Tag for ECR
docker tag bangladesh-news-scraper:latest <account-id>.dkr.ecr.<region>.amazonaws.com/bangladesh-news-scraper:latest

# Push to ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/bangladesh-news-scraper:latest
```

3. **Create ECS Task Definition**
```json
{
  "family": "bangladesh-news-scraper",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "bangladesh-news-api",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/bangladesh-news-scraper:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MONGODB_URL",
          "value": "mongodb://username:password@mongodb-cluster:27017/bangladesh_news"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bangladesh-news-scraper",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Production Configuration

### Environment Variables

```env
# Production MongoDB with authentication
MONGODB_URL=mongodb://username:password@mongodb-host:27017/bangladesh_news

# Production settings
SCRAPING_DELAY=2
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/bangladesh-news-scraper/app.log

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
```

### Security Considerations

1. **Database Security**
   - Enable MongoDB authentication
   - Use strong passwords
   - Configure firewall rules
   - Enable SSL/TLS for MongoDB connections

2. **API Security**
   - Implement rate limiting
   - Add API key authentication if needed
   - Use HTTPS only
   - Configure CORS properly

3. **Server Security**
   - Keep system updated
   - Configure firewall (UFW/iptables)
   - Use fail2ban for intrusion prevention
   - Regular security audits

### Monitoring and Logging

#### Application Monitoring

```python
# Add to main.py for production monitoring
import logging
from logging.handlers import RotatingFileHandler

# Configure production logging
if not app.debug:
    file_handler = RotatingFileHandler(
        '/var/log/bangladesh-news-scraper/app.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

#### System Monitoring

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# MongoDB monitoring
mongostat --host localhost:27017 -u newscraper -p your_password

# Application monitoring
sudo journalctl -u bangladesh-news-api -f
```

### Backup Strategy

#### Database Backup

```bash
# Create backup script
cat > /home/newscraper/backup_mongodb.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/newscraper/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="bangladesh_news_backup_$DATE"

mkdir -p $BACKUP_DIR

mongodump --host localhost:27017 \
          --username newscraper \
          --password your_secure_password \
          --db bangladesh_news \
          --out $BACKUP_DIR/$BACKUP_NAME

# Compress backup
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C $BACKUP_DIR $BACKUP_NAME
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
EOF

chmod +x /home/newscraper/backup_mongodb.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/newscraper/backup_mongodb.sh
```

### Performance Optimization

#### Database Optimization

```javascript
// MongoDB performance tuning
db.adminCommand({setParameter: 1, internalQueryExecMaxBlockingSortBytes: 335544320})

// Index optimization
db.unique_news.getIndexes()
db.unique_news.stats()

// Query performance analysis
db.unique_news.explain("executionStats").find({source: "daily_star"})
```

#### Application Optimization

```python
# Add connection pooling in production
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000
)
```

### Scaling Considerations

#### Horizontal Scaling

1. **Load Balancer Configuration**
   - Use Nginx or AWS ALB
   - Configure health checks
   - Session affinity if needed

2. **Database Scaling**
   - MongoDB replica sets
   - Sharding for large datasets
   - Read replicas for analytics

3. **Caching Layer**
   - Redis for API response caching
   - CDN for static content
   - Application-level caching

#### Vertical Scaling

- Monitor CPU and memory usage
- Optimize database queries
- Tune application parameters
- Use profiling tools

### Maintenance Procedures

#### Regular Maintenance Tasks

```bash
# Weekly maintenance script
cat > /home/newscraper/weekly_maintenance.sh << 'EOF'
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart bangladesh-news-api
sudo systemctl restart nginx

# Clean up old logs
find /var/log/bangladesh-news-scraper -name "*.log.*" -mtime +30 -delete

# Database maintenance
mongosh bangladesh_news --eval "db.runCommand({compact: 'unique_news'})"

# Check disk space
df -h

echo "Weekly maintenance completed"
EOF

chmod +x /home/newscraper/weekly_maintenance.sh
```

### Troubleshooting Production Issues

#### Common Production Issues

1. **High Memory Usage**
   ```bash
   # Monitor memory usage
   free -h
   ps aux --sort=-%mem | head
   
   # Restart application if needed
   sudo systemctl restart bangladesh-news-api
   ```

2. **Database Connection Issues**
   ```bash
   # Check MongoDB status
   sudo systemctl status mongod
   
   # Check connections
   mongosh --eval "db.serverStatus().connections"
   ```

3. **API Performance Issues**
   ```bash
   # Check API response times
   curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"
   
   # Monitor application logs
   sudo journalctl -u bangladesh-news-api -f
   ```

### Disaster Recovery

#### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Restore from backup
   mongorestore --host localhost:27017 \
                --username newscraper \
                --password your_secure_password \
                --db bangladesh_news \
                /path/to/backup/bangladesh_news
   ```

2. **Application Recovery**
   ```bash
   # Redeploy application
   cd /home/newscraper/bangladesh_news_scraper
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart bangladesh-news-api
   ```

This deployment guide provides comprehensive instructions for deploying the Bangladesh News Scraper API in production environments with proper security, monitoring, and maintenance procedures.

