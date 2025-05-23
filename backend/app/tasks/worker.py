from celery import Celery
import os
REDIS_BROKER_URL=os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "sentinel_share_worker",
    broker=REDIS_BROKER_URL,
    backend=REDIS_BROKER_URL
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)
