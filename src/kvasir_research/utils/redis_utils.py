import redis.asyncio as redis
import json
from typing import List, Literal, Dict, Any
from uuid import UUID
from pathlib import Path
from dataclasses import is_dataclass, asdict
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from kvasir_research.secrets import REDIS_URL


# Initialize Redis client
_redis_client = redis.from_url(REDIS_URL, decode_responses=False)

RunStatus = Literal["pending", "completed", "failed", "waiting", "running"]


def _pydantic_ai_bytes_to_messages(message_list: List[bytes]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for message in message_list:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message))

    return messages


def _pydantic_ai_messages_to_bytes(messages: list[ModelMessage]) -> List[bytes]:
    return [ModelMessagesTypeAdapter.dump_json(messages)]


async def save_message_history(run_id: str, message_history: List[ModelMessage]):
    key = f"{run_id}-messages"
    message_bytes = _pydantic_ai_messages_to_bytes(message_history)

    await _redis_client.delete(key)

    if message_bytes:
        await _redis_client.rpush(key, *message_bytes)


async def get_message_history(run_id: str) -> List[ModelMessage]:
    key = f"{run_id}-messages"
    message_list = await _redis_client.lrange(key, 0, -1)

    if not message_list:
        return []

    return _pydantic_ai_bytes_to_messages(message_list)


async def set_run_status(run_id: str, status: RunStatus):
    key = f"{run_id}-status"
    await _redis_client.set(key, status.encode('utf-8'))


async def get_run_status(run_id: str) -> str | None:
    key = f"{run_id}-status"
    status = await _redis_client.get(key)
    return status.decode('utf-8') if status else None


# Queue management functions
async def add_result_to_queue(run_id: str, result: str):
    key = f"{run_id}-results-queue"
    await _redis_client.rpush(key, result.encode('utf-8'))


async def get_results_queue(run_id: str) -> List[str]:
    key = f"{run_id}-results-queue"
    results = await _redis_client.lrange(key, 0, -1)
    return [r.decode('utf-8') for r in results]


async def pop_result_from_queue(run_id: str) -> str | None:
    key = f"{run_id}-results-queue"
    result = await _redis_client.lpop(key)
    return result.decode('utf-8') if result else None


async def clear_results_queue(run_id: str):
    key = f"{run_id}-results-queue"
    await _redis_client.delete(key)


# Dependency management functions
def _serialize_deps_value(value: Any) -> Any:
    """Convert special types to JSON-serializable format"""
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, Path):
        return str(value)
    elif isinstance(value, dict):
        return {k: _serialize_deps_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_deps_value(v) for v in value]
    else:
        return value


async def save_deps(run_id: str, deps: Any):
    """Save deps by converting dataclass to dictionary then JSON"""
    key = f"{run_id}-deps"
    
    if is_dataclass(deps):
        deps_dict = asdict(deps)
    elif isinstance(deps, dict):
        deps_dict = deps
    else:
        raise ValueError(f"deps must be a dataclass or dict, got {type(deps)}")
    
    # Serialize special types
    serialized_dict = _serialize_deps_value(deps_dict)
    
    await _redis_client.set(key, json.dumps(serialized_dict).encode('utf-8'))


async def get_saved_deps(run_id: str) -> Dict[str, Any] | None:
    """Get saved deps as dictionary (caller must reconstruct dataclass)"""
    key = f"{run_id}-deps"
    deps_bytes = await _redis_client.get(key)
    
    if not deps_bytes:
        return None
    
    return json.loads(deps_bytes.decode('utf-8'))


async def delete_deps(run_id: str):
    key = f"{run_id}-deps"
    await _redis_client.delete(key)


async def save_analysis(run_id: str, analysis_content: str):
    key = f"{run_id}-analysis"
    await _redis_client.set(key, analysis_content.encode('utf-8'))


async def get_analysis(run_id: str) -> str | None:
    key = f"{run_id}-analysis"
    analysis = await _redis_client.get(key)
    return analysis.decode('utf-8') if analysis else None
