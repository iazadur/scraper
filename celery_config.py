import os
from config.settings import REDIS_URL

# Celery configuration settings
broker_url = REDIS_URL
result_backend = REDIS_URL

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000

# Result backend settings
result_expires = 3600
