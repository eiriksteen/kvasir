from celery import Celery
from synesis_api.secrets import CELERY_BROKER_URL, CELERY_BACKEND_URL

celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
    include=[
        "src.synesis_api.modules.integration.service",
        "src.synesis_api.modules.analysis.service",
        "src.synesis_api.modules.automation.service"
    ]
)
