import redis.asyncio as redis
import json
import pickle
from typing import List, Literal, Dict, Any
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
async def save_deps(run_id: str, deps: Any):
    key = f"{run_id}-deps"
    await _redis_client.set(key, pickle.dumps(deps))


async def get_saved_deps(run_id: str) -> Any | None:
    key = f"{run_id}-deps"
    deps_bytes = await _redis_client.get(key)
    return pickle.loads(deps_bytes) if deps_bytes else None


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
