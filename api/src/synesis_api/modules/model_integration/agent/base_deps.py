import uuid
import httpx
import redis
from synesis_api.secrets import GITHUB_TOKEN
from synesis_api.redis import get_redis
from dataclasses import dataclass


@dataclass(kw_only=True)
class BaseDeps:
    model_id: str
    integration_id: uuid.UUID
    source: str  # Literal["github", "pip"]
    container_name: str
    current_script: str | None = None
    redis_stream: redis.Redis = get_redis()
    client: httpx.AsyncClient = httpx.AsyncClient()
    github_token: str = GITHUB_TOKEN
    cwd: str | None = None
    run_pylint: bool = False
    history_summary: str | None = None
    history_cutoff_index: int = 1
