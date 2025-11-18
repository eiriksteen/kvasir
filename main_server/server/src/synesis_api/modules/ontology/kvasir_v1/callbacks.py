import json
from uuid import UUID
from typing import Literal, List, Dict
from datetime import datetime, timezone
from pydantic_ai.models import ModelMessage
from taskiq import TaskiqState, TaskiqEvents
from pydantic_ai.messages import ModelMessagesTypeAdapter

from synesis_api.database.service import execute
from synesis_api.modules.runs.service import get_runs, create_run as create_run_service, update_run_status, create_run_message
from synesis_api.modules.runs.schema import RunMessageCreate, RunCreate, RunStatusUpdate
from synesis_api.modules.runs.models import run
from synesis_api.modules.ontology.kvasir_v1.service import (
    create_results_queue_item,
    get_latest_results_queue_item,
    update_results_queue_item_content,
    delete_results_queue_item,
    create_deps,
    get_latest_deps,
    create_result,
    get_latest_result,
    create_pydantic_ai_messages,
    get_pydantic_ai_messages,
)
from synesis_api.modules.ontology.kvasir_v1.schema import (
    ResultsQueueCreate,
    DepsCreate,
    ResultCreate,
)
from synesis_api.modules.ontology.service import create_ontology_for_user
from kvasir_ontology.ontology import Ontology
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.broker import logger, v1_broker


class ApplicationCallbacks(KvasirV1Callbacks):

    def create_ontology(self, user_id: UUID, mount_group_id: UUID, bearer_token: str | None = None) -> Ontology:
        return create_ontology_for_user(user_id, mount_group_id, bearer_token)

    async def get_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        runs_objs = await get_runs(run_id=run_id)
        if len(runs_objs) == 0:
            raise ValueError(f"Run with id {run_id} not found")

        return runs_objs[0].status

    async def set_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        await update_run_status(run_id, RunStatusUpdate(run_id=run_id, status=status))
        return status

    async def create_run(self, user_id: UUID, project_id: UUID, run_type: Literal["swe", "analysis", "chart", "extraction", "kvasir"]) -> UUID:
        run_create = RunCreate(
            type=run_type,
            run_name=f"{run_type} run",
            plan_and_deliverable_description_for_user="",
            plan_and_deliverable_description_for_agent="",
            initial_status="running",
            project_id=project_id,
        )
        run_record = await create_run_service(user_id, run_create)
        return run_record.id

    async def complete_run(self, run_id: UUID, output: str) -> None:
        await execute(
            run.update().where(run.c.id == run_id).values(
                status="completed",
                completed_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

    async def fail_run(self, run_id: UUID, error: str) -> None:
        await execute(
            run.update().where(run.c.id == run_id).values(
                status="failed",
                completed_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

    async def get_results_queue(self, run_id: UUID) -> List[str]:
        queue_item = await get_latest_results_queue_item(run_id)
        if queue_item:
            return queue_item.content
        return []

    async def pop_result_from_queue(self, run_id: UUID) -> str:
        queue_item = await get_latest_results_queue_item(run_id)
        if not queue_item or not queue_item.content:
            return ""

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
        message_bytes = ModelMessagesTypeAdapter.dump_json(message_history)
        await create_pydantic_ai_messages(run_id, [message_bytes])

    async def get_message_history(self, run_id: UUID) -> List[ModelMessage] | None:
        messages = await get_pydantic_ai_messages(run_id)
        return messages if messages else None

    async def log(self, run_id: UUID, message: str, type: Literal["result", "tool_call", "error"]) -> None:
        log_message = f"[{run_id}] [{type.upper()}] {message}"
        logger.info(log_message)
        # Also print directly to ensure visibility
        print(log_message, flush=True)
        await create_run_message(RunMessageCreate(
            run_id=run_id,
            content=message,
            type=type
        ))


@v1_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    state.callbacks = ApplicationCallbacks()
