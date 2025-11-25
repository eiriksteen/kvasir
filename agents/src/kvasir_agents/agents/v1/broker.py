import os
import sys
import logging
import importlib
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from kvasir_agents.app_secrets import REDIS_URL


# TODO: TLS!

# Configure the logger explicitly to ensure it outputs to console
logger = logging.getLogger("kvasir")
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers.clear()

# Add console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Prevent propagation to root logger to avoid duplicate messages
logger.propagate = False

v1_result_backend = RedisAsyncResultBackend(redis_url=REDIS_URL)
v1_broker = RedisStreamBroker(
    url=REDIS_URL).with_result_backend(v1_result_backend)

callbacks_module = os.getenv("KVASIR_CALLBACKS_MODULE")
if callbacks_module:
    try:
        importlib.import_module(callbacks_module)
        logger.info(f"Imported callbacks module: {callbacks_module}")
    except ImportError as e:
        logger.warning(
            f"Failed to import callbacks module {callbacks_module}: {e}")
