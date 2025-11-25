import redis.asyncio as redis
import json
from typing import List, Literal, Dict, Any
from uuid import UUID
from pathlib import Path
from collections import OrderedDict
from dataclasses import is_dataclass, asdict, fields
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from kvasir_agents.app_secrets import REDIS_URL


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


async def save_message_history(run_id: UUID, message_history: List[ModelMessage]):
    key = f"{str(run_id)}-messages"
    message_bytes = _pydantic_ai_messages_to_bytes(message_history)

    await _redis_client.delete(key)

    if message_bytes:
        await _redis_client.rpush(key, *message_bytes)


async def get_message_history(run_id: UUID) -> List[ModelMessage]:
    key = f"{str(run_id)}-messages"
    message_list = await _redis_client.lrange(key, 0, -1)

    if not message_list:
        return []

    return _pydantic_ai_bytes_to_messages(message_list)


async def set_run_status(run_id: UUID, status: RunStatus):
    key = f"{str(run_id)}-status"
    await _redis_client.set(key, status.encode('utf-8'))


async def get_run_status(run_id: UUID) -> str | None:
    key = f"{str(run_id)}-status"
    status = await _redis_client.get(key)
    return status.decode('utf-8') if status else None


# Queue management functions
async def add_result_to_queue(run_id: UUID, result: str):
    key = f"{str(run_id)}-results-queue"
    await _redis_client.rpush(key, result.encode('utf-8'))


async def get_results_queue(run_id: UUID) -> List[str]:
    key = f"{str(run_id)}-results-queue"
    results = await _redis_client.lrange(key, 0, -1)
    return [r.decode('utf-8') for r in results]


async def pop_result_from_queue(run_id: UUID) -> str | None:
    key = f"{str(run_id)}-results-queue"
    result = await _redis_client.lpop(key)
    return result.decode('utf-8') if result else None


async def clear_results_queue(run_id: UUID):
    key = f"{str(run_id)}-results-queue"
    await _redis_client.delete(key)


# Dependency management functions
def _serialize_deps_value(value: Any) -> Any:
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


def _dataclass_to_dict_excluding_fields(obj: Any, exclude_fields: set[str]) -> Dict[str, Any]:
    if not is_dataclass(obj):
        raise ValueError(f"Expected dataclass, got {type(obj)}")

    result = {}
    for field_info in fields(obj):
        if field_info.name in exclude_fields:
            continue

        value = getattr(obj, field_info.name)
        if isinstance(value, (dict, OrderedDict)):
            result[field_info.name] = dict(value)
        elif isinstance(value, (list, tuple)):
            result[field_info.name] = list(value) if isinstance(
                value, list) else tuple(value)
        else:
            result[field_info.name] = value

    return result


async def save_deps(run_id: UUID, deps: Any):
    key = f"{str(run_id)}-deps"

    if is_dataclass(deps):
        deps_dict = _dataclass_to_dict_excluding_fields(
            deps, exclude_fields={"sandbox"})
    elif isinstance(deps, dict):
        deps_dict = dict(deps)
        deps_dict.pop("sandbox", None)
    else:
        raise ValueError(f"deps must be a dataclass or dict, got {type(deps)}")

    serialized_dict = _serialize_deps_value(deps_dict)

    await _redis_client.set(key, json.dumps(serialized_dict).encode('utf-8'))


async def get_saved_deps(run_id: UUID) -> Dict[str, Any] | None:
    key = f"{str(run_id)}-deps"
    deps_bytes = await _redis_client.get(key)

    if not deps_bytes:
        return None

    return json.loads(deps_bytes.decode('utf-8'))


async def delete_deps(run_id: UUID):
    key = f"{str(run_id)}-deps"
    await _redis_client.delete(key)


async def save_analysis(run_id: UUID, analysis_content: str):
    key = f"{str(run_id)}-analysis"
    await _redis_client.set(key, analysis_content.encode('utf-8'))


async def get_analysis(run_id: UUID) -> str | None:
    key = f"{str(run_id)}-analysis"
    analysis = await _redis_client.get(key)
    return analysis.decode('utf-8') if analysis else None


async def save_swe_result(run_id: UUID, swe_result: str):
    key = f"{str(run_id)}-swe-result"
    await _redis_client.set(key, swe_result.encode('utf-8'))


async def get_swe_result(run_id: UUID) -> str | None:
    key = f"{str(run_id)}-swe-result"
    swe_result = await _redis_client.get(key)
    return swe_result.decode('utf-8') if swe_result else None
