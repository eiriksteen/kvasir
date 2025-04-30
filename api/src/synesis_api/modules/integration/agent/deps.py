from dataclasses import dataclass
from pathlib import Path
import redis
import uuid


@dataclass
class IntegrationAgentDeps:
    job_id: uuid.UUID
    data_description: str
    api_key: str
    redis_stream: redis.Redis
