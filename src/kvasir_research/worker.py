import logging
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from kvasir_research.secrets import REDIS_URL


# TODO: TLS!

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("taskiq")

result_backend = RedisAsyncResultBackend(redis_url=REDIS_URL)
broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(result_backend)
