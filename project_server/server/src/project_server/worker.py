import logging
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from project_server.app_secrets import TASKIQ_BROKER_URL, TASKIQ_BACKEND_URL


# TODO: TLS!

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("taskiq")

result_backend = RedisAsyncResultBackend(redis_url=TASKIQ_BACKEND_URL)
broker = RedisStreamBroker(
    url=TASKIQ_BROKER_URL).with_result_backend(result_backend)
