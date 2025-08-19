#!/bin/bash

# Startup script for Bangladesh News Scraper

set -e

# Wait for dependencies to be ready
echo "Waiting for MongoDB to be ready..."
while ! nc -z mongodb 27017; do
  sleep 1
done
echo "MongoDB is ready!"

echo "Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Run the application based on the service type
case "$1" in
  "app")
    echo "Starting FastAPI application..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
  "worker")
    echo "Starting Celery worker..."
    exec celery -A scrapers.scraper_manager worker --loglevel=info
    ;;
  "beat")
    echo "Starting Celery beat scheduler..."
    exec celery -A scrapers.scraper_manager beat --loglevel=info
    ;;
  "flower")
    echo "Starting Flower monitoring..."
    exec celery -A scrapers.scraper_manager flower --port=5555
    ;;
  *)
    echo "Usage: $0 {app|worker|beat|flower}"
    exit 1
    ;;
esac
