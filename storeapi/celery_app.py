"""
Celery configuration module for the Store API application.
This module initializes and configures the Celery instance for background task processing.
"""
from celery import Celery

from storeapi.config import config

celery_app = Celery(
    "storeapi",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["storeapi"])
