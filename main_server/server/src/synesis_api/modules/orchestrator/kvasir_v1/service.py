import uuid
import json
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import insert, select, delete, update

from synesis_api.database.service import execute, fetch_all, fetch_one
from synesis_api.modules.orchestrator.kvasir_v1.models import (
    results_queue,
    deps,
    result,
    pydantic_ai_message
)
from synesis_api.modules.orchestrator.kvasir_v1.schema import (
    ResultsQueueInDB,
    ResultsQueueCreate,
    DepsInDB,
    DepsCreate,
    ResultInDB,
    ResultCreate,
    PydanticAIMessageInDB,
    PydanticAIMessageCreate,
    DEP_TYPE_LITERAL,
    RESULT_TYPE_LITERAL,
)


async def create_results_queue_item(create: ResultsQueueCreate) -> ResultsQueueInDB:
    results_queue_obj = ResultsQueueInDB(
        id=uuid.uuid4(),
        **create.model_dump(),
        created_at=datetime.now(timezone.utc)
    )

    await execute(insert(results_queue).values(**results_queue_obj.model_dump()), commit_after=True)

    return results_queue_obj


async def get_results_queue_items(run_id: uuid.UUID) -> List[ResultsQueueInDB]:
    query = select(results_queue).where(results_queue.c.run_id ==
                                        run_id).order_by(results_queue.c.created_at)
    records = await fetch_all(query)

    return [ResultsQueueInDB(**record) for record in records]


async def delete_results_queue_item(item_id: uuid.UUID) -> None:
    await execute(delete(results_queue).where(results_queue.c.id == item_id), commit_after=True)


async def get_latest_results_queue_item(run_id: uuid.UUID) -> Optional[ResultsQueueInDB]:
    query = select(results_queue).where(results_queue.c.run_id == run_id).order_by(
        results_queue.c.created_at.desc()).limit(1)

    record = await fetch_one(query)

    if record:
        return ResultsQueueInDB(**record)
    return None


async def update_results_queue_item_content(item_id: uuid.UUID, content: List[str]) -> None:
    await execute(
        update(results_queue)
        .where(results_queue.c.id == item_id)
        .values(content=content),
        commit_after=True
    )


async def create_deps(create: DepsCreate) -> DepsInDB:
    deps_obj = DepsInDB(
        id=uuid.uuid4(),
        **create.model_dump(),
        created_at=datetime.now(timezone.utc)
    )

    await execute(insert(deps).values(**deps_obj.model_dump()), commit_after=True)

    return deps_obj


async def get_deps(run_id: uuid.UUID, type: Optional[DEP_TYPE_LITERAL] = None) -> List[DepsInDB]:
    query = select(deps).where(deps.c.run_id == run_id)
    if type:
        query = query.where(deps.c.type == type)
    query = query.order_by(deps.c.created_at)

    records = await fetch_all(query)

    return [DepsInDB(**record) for record in records]


async def get_latest_deps(run_id: uuid.UUID, type: Optional[DEP_TYPE_LITERAL] = None) -> Optional[DepsInDB]:
    query = select(deps).where(deps.c.run_id == run_id)
    if type:
        query = query.where(deps.c.type == type)
    query = query.order_by(deps.c.created_at.desc()).limit(1)

    record = await fetch_one(query)

    if record:
        return DepsInDB(**record)
    return None


async def create_result(create: ResultCreate) -> ResultInDB:
    result_obj = ResultInDB(
        id=uuid.uuid4(),
        **create.model_dump(),
        created_at=datetime.now(timezone.utc)
    )

    await execute(insert(result).values(**result_obj.model_dump()), commit_after=True)

    return result_obj


async def get_results(run_id: uuid.UUID, type: Optional[RESULT_TYPE_LITERAL] = None) -> List[ResultInDB]:
    query = select(result).where(result.c.run_id == run_id)
    if type:
        query = query.where(result.c.type == type)
    query = query.order_by(result.c.created_at)

    records = await fetch_all(query)

    return [ResultInDB(**record) for record in records]


async def get_latest_result(run_id: uuid.UUID, type: Optional[RESULT_TYPE_LITERAL] = None) -> Optional[ResultInDB]:
    query = select(result).where(result.c.run_id == run_id)
    if type:
        query = query.where(result.c.type == type)
    query = query.order_by(result.c.created_at.desc()).limit(1)

    record = await fetch_one(query)

    if record:
        return ResultInDB(**record)
    return None


async def create_pydantic_ai_message(create: PydanticAIMessageCreate) -> PydanticAIMessageInDB:
    pydantic_ai_message_obj = PydanticAIMessageInDB(
        id=uuid.uuid4(),
        run_id=create.run_id,
        message_list=create.content,
        created_at=datetime.now(timezone.utc)
    )

    await execute(insert(pydantic_ai_message).values(**pydantic_ai_message_obj.model_dump()), commit_after=True)

    return pydantic_ai_message_obj


async def get_pydantic_ai_messages(run_id: uuid.UUID) -> List[PydanticAIMessageInDB]:
    query = select(pydantic_ai_message).where(
        pydantic_ai_message.c.run_id == run_id).order_by(pydantic_ai_message.c.created_at)
    records = await fetch_all(query)

    return [PydanticAIMessageInDB(**record) for record in records]


async def get_latest_pydantic_ai_message(run_id: uuid.UUID) -> Optional[PydanticAIMessageInDB]:
    query = select(pydantic_ai_message).where(pydantic_ai_message.c.run_id ==
                                              run_id).order_by(pydantic_ai_message.c.created_at.desc()).limit(1)

    record = await fetch_one(query)

    if record:
        return PydanticAIMessageInDB(**record)
    return None
