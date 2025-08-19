import os
from celery import Celery
from config.settings import REDIS_URL

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('CELERY_CONFIG_MODULE', 'celery_config')

app = Celery('bangladesh_news_scraper')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('celery_config', namespace='CELERY')

# Load task modules from all registered Django app configs.
# app.autodiscover_tasks(['scrapers.tasks'])

# Manually import tasks to avoid module discovery issues
try:
    from scrapers.tasks import scrape_all_news, deduplicate_news, update_geolocation
except ImportError:
    # Tasks module not available during development
    pass

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'scrape-news-every-hour': {
        'task': 'scrapers.tasks.scrape_all_news',
        'schedule': 60.0 * 60.0,  # Every hour
    },
}

app.conf.timezone = 'UTC'
