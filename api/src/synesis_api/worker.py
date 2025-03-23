from celery import Celery
from .secrets import CELERY_BROKER_URL, CELERY_BACKEND_URL

celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
    include=[
        "src.synesis_api.data_integration.service",
        "src.synesis_api.eda.service"
    ]
)