import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import insert, select, delete
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.model_integration.schema import ModelIntegrationJobResultInDB
from synesis_api.modules.model_integration.models import model_integration_job_result
from synesis_api.database.service import execute, fetch_one
from synesis_api.redis import get_redis


def _get_stage_output_cache_key(model_id: str, source: str, stage: str) -> str:
    """Generate cache key for a specific stage output"""
    return f"model_integration:{model_id}:{source}:{stage}"


def _get_message_history_cache_key(model_id: str, source: str) -> str:
    """Generate cache key for message history"""
    return f"model_integration:{model_id}:{source}:message_history"


async def save_stage_output_to_cache(
    model_id: str,
    source: str,
    stage: str,
    output_data: dict,
    message_history: bytes | None = None,
    ttl: int = 86400  # 24 hours default TTL
) -> None:
    """Save stage output to Redis cache"""
    cache = get_redis()
    cache_key = _get_stage_output_cache_key(model_id, source, stage)
    message_history_cache_key = _get_message_history_cache_key(
        model_id, source)

    # Add timestamp for cache invalidation
    output_with_metadata = {
        "output": output_data,
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "source": source,
        "stage": stage
    }

    await cache.setex(
        cache_key,
        ttl,
        json.dumps(output_with_metadata)
    )

    if message_history:
        await cache.setex(
            message_history_cache_key,
            ttl,
            message_history
        )


async def get_stage_output_from_cache(
    model_id: str,
    source: str,
    stage: str
) -> dict | None:
    """Retrieve stage output from Redis cache"""
    cache = get_redis()
    cache_key = _get_stage_output_cache_key(model_id, source, stage)

    cached_data = await cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def get_message_history_from_cache(model_id: str, source: str) -> list[ModelMessage] | None:
    """Retrieve message history from Redis cache"""
    cache = get_redis()
    cache_key = _get_message_history_cache_key(model_id, source)
    cached_data = await cache.get(cache_key)
    if cached_data:
        return ModelMessagesTypeAdapter.validate_json(cached_data)
    return None


async def create_model_integration_result(job_id: uuid.UUID, model_id: uuid.UUID):

    result = ModelIntegrationJobResultInDB(
        job_id=job_id,
        model_id=model_id
    )

    await execute(
        insert(model_integration_job_result).values(
            result.model_dump()),
        commit_after=True
    )


async def delete_model_integration_result(job_id: uuid.UUID):
    await execute(
        delete(model_integration_job_result).where(
            model_integration_job_result.c.job_id == job_id),
        commit_after=True
    )


async def get_model_integration_job_results(job_id: uuid.UUID) -> ModelIntegrationJobResultInDB:
    # get results from model_integration_jobs_results
    results = await fetch_one(
        select(model_integration_job_result).where(
            model_integration_job_result.c.job_id == job_id),
        commit_after=True
    )

    return ModelIntegrationJobResultInDB(**results)


async def get_model_id_from_job_id(job_id: uuid.UUID) -> uuid.UUID:
    model_id = await fetch_one(
        select(model_integration_job_result).where(
            model_integration_job_result.c.job_id == job_id),
        commit_after=True
    )

    return model_id["model_id"]
