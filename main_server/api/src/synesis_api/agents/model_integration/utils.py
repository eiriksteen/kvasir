import json
from datetime import datetime, timezone
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
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
