import json
from uuid import UUID
from typing import Literal, List, Dict
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


from synesis_api.modules.runs.service import get_runs, update_run_status, create_run_message
from synesis_schemas.main_server import RunMessageCreate
from synesis_api.modules.orchestrator.kvasir_v1.service import (
    create_results_queue_item,
    get_latest_results_queue_item,
    update_results_queue_item_content,
    delete_results_queue_item,
    create_deps,
    get_latest_deps,
    create_result,
    get_latest_result,
    create_pydantic_ai_message,
    get_latest_pydantic_ai_message,
)
from synesis_api.modules.orchestrator.kvasir_v1.schema import (
    ResultsQueueCreate,
    DepsCreate,
    ResultCreate,
    PydanticAIMessageCreate
)


from kvasir_research.agents.kvasir_v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.kvasir_v1.broker import logger


class ApplicationCallbacks(KvasirV1Callbacks):

    async def check_orchestrator_run_exists(self, run_id: UUID) -> bool:
        runs_objs = await get_runs(run_id=run_id)
        return len(runs_objs) > 0

    async def get_orchestrator_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        runs_objs = await get_runs(run_id=run_id)
        if len(runs_objs) == 0:
            raise ValueError(f"Run with id {run_id} not found")

        return runs_objs[0].status

    async def set_orchestrator_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        await update_run_status(run_id=run_id, status=status)
        return status

    async def get_results_queue(self, run_id: UUID) -> List[str]:
        queue_item = await get_latest_results_queue_item(run_id)
        if queue_item:
            return queue_item.content
        return []

    async def pop_result_from_queue(self, run_id: UUID) -> str:
        queue_item = await get_latest_results_queue_item(run_id)
        if not queue_item or not queue_item.content:
            raise ValueError(f"No results in queue for run_id {run_id}")

        content_list = list(queue_item.content)
        result = content_list.pop(0)

        if content_list:
            await update_results_queue_item_content(queue_item.id, content_list)
        else:
            await delete_results_queue_item(queue_item.id)

        return result

    async def add_result_to_queue(self, run_id: UUID, result: str) -> None:
        queue_item = await get_latest_results_queue_item(run_id)
        if queue_item:
            new_content = queue_item.content + [result]
            await update_results_queue_item_content(queue_item.id, new_content)
        else:
            await create_results_queue_item(ResultsQueueCreate(run_id=run_id, content=[result]))

    async def save_orchestrator_deps(self, run_id: UUID, deps: Dict) -> None:
        await create_deps(DepsCreate(
            run_id=run_id,
            type="orchestrator",
            content=json.dumps(deps)
        ))

    async def load_orchestrator_deps(self, run_id: UUID) -> Dict:
        deps_obj = await get_latest_deps(run_id, type="orchestrator")
        if deps_obj:
            return json.loads(deps_obj.content)
        return {}

    async def save_swe_deps(self, run_id: UUID, deps: Dict) -> None:
        await create_deps(DepsCreate(
            run_id=run_id,
            type="swe",
            content=json.dumps(deps)
        ))

    async def load_swe_deps(self, run_id: UUID) -> Dict:
        deps_obj = await get_latest_deps(run_id, type="swe")
        if deps_obj:
            return json.loads(deps_obj.content)
        return {}

    async def save_swe_result(self, run_id: UUID, result: str) -> None:
        await create_result(ResultCreate(
            run_id=run_id,
            type="swe",
            content=result
        ))

    async def get_swe_result(self, run_id: UUID) -> str:
        result_obj = await get_latest_result(run_id, type="swe")
        if result_obj:
            return result_obj.content
        raise ValueError(f"No swe result found for run_id {run_id}")

    async def save_analysis_deps(self, run_id: UUID, deps: Dict) -> None:
        await create_deps(DepsCreate(
            run_id=run_id,
            type="analysis",
            content=json.dumps(deps)
        ))

    async def load_analysis_deps(self, run_id: UUID) -> Dict:
        deps_obj = await get_latest_deps(run_id, type="analysis")
        if deps_obj:
            return json.loads(deps_obj.content)
        return {}

    async def save_analysis_result(self, run_id: UUID, result: str) -> None:
        await create_result(ResultCreate(
            run_id=run_id,
            type="analysis",
            content=result
        ))

    async def get_analysis_result(self, run_id: UUID) -> str:
        result_obj = await get_latest_result(run_id, type="analysis")
        if result_obj:
            return result_obj.content
        raise ValueError(f"No analysis result found for run_id {run_id}")

    async def save_message_history(self, run_id: UUID, message_history: List[ModelMessage]) -> None:
        message_json = ModelMessagesTypeAdapter.dump_json(message_history)
        await create_pydantic_ai_message(PydanticAIMessageCreate(
            run_id=run_id,
            content=message_json
        ))

    async def get_message_history(self, run_id: UUID) -> List[ModelMessage]:
        message_obj = await get_latest_pydantic_ai_message(run_id)
        if message_obj:
            return ModelMessagesTypeAdapter.validate_json(message_obj.message_list)
        return []

    async def log(self, run_id: UUID, message: str, type: Literal["tool_call", "result", "error"]) -> None:
        logger.info(f"[{run_id}] {message}")
        await create_run_message(RunMessageCreate(
            run_id=run_id,
            content=message,
            type=type
        ))
