import json
import uuid
from uuid import UUID
from typing import Literal, List, Dict, Optional
from datetime import datetime, timezone
from collections import OrderedDict
from pydantic_ai.models import ModelMessage
from taskiq import TaskiqState, TaskiqEvents
from pydantic_ai.messages import ModelMessagesTypeAdapter
from sqlalchemy import insert, select, delete, update

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.kvasir_v1.models import (
    run,
    swe_run,
    analysis_run,
    result,
    run_message,
    results_queue,
    deps,
    pydantic_ai_message
)
from synesis_api.modules.ontology.service import create_ontology_for_user
from kvasir_ontology.ontology import Ontology
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.broker import logger, v1_broker
from kvasir_research.agents.v1.data_model import (
    AnalysisRun,
    SweRun,
    RunBase,
    RunCreate,
    RunMessageCreate,
    RunMessageBase,
    ResultsQueueCreate,
    ResultsQueue,
    DepsCreate,
    DepsBase,
    ResultCreate,
    ResultBase,
    PydanticAIMessage,
    RUN_TYPE_LITERAL,
    RESULT_TYPE_LITERAL,
    RUN_STATUS_LITERAL,
)


class ApplicationCallbacks(KvasirV1Callbacks):

    def create_ontology(self, user_id: UUID, mount_group_id: UUID, bearer_token: str | None = None) -> Ontology:
        return create_ontology_for_user(user_id, mount_group_id, bearer_token)

    async def get_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        query = select(run).where(run.c.id == run_id)
        records = await fetch_all(query)
        if len(records) == 0:
            raise ValueError(f"Run with id {run_id} not found")
        return RunBase(**records[0]).status

    async def set_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        await execute(
            update(run)
            .where(run.c.id == run_id)
            .values(status=status),
            commit_after=True
        )
        return status

    async def _create_run(self, user_id: uuid.UUID, create: RunCreate) -> RunBase:
        create_dict = create.model_dump(exclude={"initial_status", "id"})
        run_obj = RunBase(
            id=create.id if create.id else uuid.uuid4(),
            user_id=user_id,
            status=create.initial_status,
            description=None,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            **create_dict
        )
        await execute(insert(run).values(**run_obj.model_dump()), commit_after=True)
        return run_obj

    async def create_swe_run(self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> UUID:
        run_create = RunCreate(
            type="swe",
            run_name=run_name or "swe run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self._create_run(user_id, run_create)

        await execute(
            insert(swe_run).values(
                run_id=run_record.id,
                kvasir_run_id=kvasir_run_id,
                created_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

        return run_record.id

    async def create_analysis_run(self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, analysis_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> UUID:
        run_create = RunCreate(
            type="analysis",
            run_name=run_name or "analysis run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self._create_run(user_id, run_create)

        await execute(
            insert(analysis_run).values(
                run_id=run_record.id,
                analysis_id=analysis_id,
                kvasir_run_id=kvasir_run_id,
                created_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

        return run_record.id

    async def create_kvasir_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> UUID:
        run_create = RunCreate(
            type="kvasir",
            run_name=run_name or "kvasir run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self._create_run(user_id, run_create)
        return run_record.id

    async def create_extraction_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> UUID:
        run_create = RunCreate(
            type="extraction",
            run_name=run_name or "extraction run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self._create_run(user_id, run_create)
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

    async def _get_latest_results_queue_item(self, run_id: uuid.UUID) -> Optional[ResultsQueue]:
        query = select(results_queue).where(results_queue.c.run_id == run_id).order_by(
            results_queue.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return ResultsQueue(**record)
        return None

    async def get_results_queue(self, run_id: UUID) -> List[str]:
        queue_item = await self._get_latest_results_queue_item(run_id)
        if queue_item:
            return queue_item.content
        return []

    async def pop_result_from_queue(self, run_id: UUID) -> str:
        queue_item = await self._get_latest_results_queue_item(run_id)
        if not queue_item or not queue_item.content:
            return ""

        content_list = list(queue_item.content)
        result = content_list.pop(0)

        if content_list:
            await execute(
                update(results_queue)
                .where(results_queue.c.id == queue_item.id)
                .values(content=content_list),
                commit_after=True
            )
        else:
            await execute(delete(results_queue).where(results_queue.c.id == queue_item.id), commit_after=True)

        return result

    async def add_result_to_queue(self, run_id: UUID, result: str) -> None:
        queue_item = await self._get_latest_results_queue_item(run_id)
        if queue_item:
            new_content = queue_item.content + [result]
            await execute(
                update(results_queue)
                .where(results_queue.c.id == queue_item.id)
                .values(content=new_content),
                commit_after=True
            )
        else:
            results_queue_obj = ResultsQueue(
                id=uuid.uuid4(),
                run_id=run_id,
                content=[result],
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(results_queue).values(**results_queue_obj.model_dump()), commit_after=True)

    async def _get_latest_deps(self, run_id: uuid.UUID, type: Optional[RUN_TYPE_LITERAL] = None) -> Optional[DepsBase]:
        query = select(deps).where(deps.c.run_id == run_id)
        if type:
            query = query.where(deps.c.type == type)
        query = query.order_by(deps.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return DepsBase(**record)
        return None

    async def save_deps(self, run_id: UUID, deps: Dict, type: Literal["swe", "analysis", "kvasir"]) -> None:
        deps_obj = DepsBase(
            id=uuid.uuid4(),
            run_id=run_id,
            type=type,
            content=json.dumps(deps),
            created_at=datetime.now(timezone.utc)
        )
        await execute(insert(deps).values(**deps_obj.model_dump()), commit_after=True)

    async def load_deps(self, run_id: UUID, type: Literal["swe", "analysis", "kvasir"]) -> Dict:
        deps_obj = await self._get_latest_deps(run_id, type=type)
        if deps_obj:
            deps_dict = json.loads(deps_obj.content)

            # For analysis, convert notebook dict to OrderedDict
            if type == "analysis" and "notebook" in deps_dict:
                notebook_raw = deps_dict.get("notebook", {})
                notebook = OrderedDict()
                for k, v in notebook_raw.items():
                    if isinstance(v, list):
                        # Convert list back to tuple for OrderedDict
                        notebook[k] = tuple(v)
                    else:
                        notebook[k] = v
                deps_dict["notebook"] = notebook

            return deps_dict
        return {}

    async def _get_latest_result(self, run_id: uuid.UUID, type: Optional[RESULT_TYPE_LITERAL] = None) -> Optional[ResultBase]:
        query = select(result).where(result.c.run_id == run_id)
        if type:
            query = query.where(result.c.type == type)
        query = query.order_by(result.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return ResultBase(**record)
        return None

    async def save_result(self, run_id: UUID, result: str, type: Literal["swe", "analysis", "kvasir"]) -> None:
        result_obj = ResultBase(
            id=uuid.uuid4(),
            run_id=run_id,
            type=type,
            content=result,
            created_at=datetime.now(timezone.utc)
        )
        await execute(insert(result).values(**result_obj.model_dump()), commit_after=True)

    async def get_result(self, run_id: UUID, type: Literal["swe", "analysis", "kvasir"]) -> str:
        result_obj = await self._get_latest_result(run_id, type=type)
        if result_obj:
            return result_obj.content
        raise ValueError(f"No {type} result found for run_id {run_id}")

    async def get_analysis_run(self, analysis_id: UUID) -> AnalysisRun:
        query = select(
            run,
            analysis_run.c.analysis_id,
            analysis_run.c.kvasir_run_id
        ).select_from(
            analysis_run.join(run, analysis_run.c.run_id == run.c.id)
        ).where(analysis_run.c.analysis_id == analysis_id)

        record = await fetch_one(query)
        if not record:
            raise ValueError(
                f"Analysis run with analysis_id {analysis_id} not found")

        run_base = RunBase(**record)

        result_obj = await self._get_latest_result(run_base.id, type="analysis")
        if not result_obj:
            raise ValueError(
                f"No analysis result found for run_id {run_base.id}")

        return AnalysisRun(
            **run_base.model_dump(),
            analysis_id=record["analysis_id"],
            kvasir_run_id=record["kvasir_run_id"],
            result=result_obj
        )

    async def get_swe_run(self, swe_run_id: UUID) -> SweRun:
        query = select(
            run,
            swe_run.c.kvasir_run_id
        ).select_from(
            swe_run.join(run, swe_run.c.run_id == run.c.id)
        ).where(swe_run.c.run_id == swe_run_id)

        record = await fetch_one(query)
        if not record:
            raise ValueError(f"SWE run with id {swe_run_id} not found")

        run_base = RunBase(**record)

        result_obj = await self._get_latest_result(run_base.id, type="swe")
        if not result_obj:
            raise ValueError(f"No swe result found for run_id {run_base.id}")

        return SweRun(
            **run_base.model_dump(),
            kvasir_run_id=record["kvasir_run_id"],
            result=result_obj
        )

    async def save_message_history(self, run_id: UUID, message_history: List[ModelMessage]) -> None:
        message_bytes = ModelMessagesTypeAdapter.dump_json(message_history)
        pydantic_ai_message_records = [PydanticAIMessage(
            id=uuid.uuid4(),
            run_id=run_id,
            message_list=message_bytes,
            created_at=datetime.now(timezone.utc)
        )]
        await execute(insert(pydantic_ai_message).values([record.model_dump() for record in pydantic_ai_message_records]), commit_after=True)

    async def get_message_history(self, run_id: UUID) -> List[ModelMessage] | None:
        c = await fetch_all(
            select(pydantic_ai_message).where(
                pydantic_ai_message.c.run_id == run_id)
        )
        messages: list[ModelMessage] = []
        for message in c:
            messages.extend(
                ModelMessagesTypeAdapter.validate_json(message["message_list"]))
        return messages if messages else None

    async def log(self, run_id: UUID, message: str, type: Literal["result", "tool_call", "error"]) -> None:
        log_message = f"[{run_id}] [{type.upper()}] {message}"
        logger.info(log_message)
        await self.create_run_message(RunMessageCreate(
            run_id=run_id,
            content=message,
            type=type
        ))

    # Methods needed by router - these are public instance methods
    async def get_runs(
        self,
        user_id: uuid.UUID,
        run_id: Optional[uuid.UUID] = None,
        run_ids: Optional[List[uuid.UUID]] = None,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        filter_status: Optional[List[str]] = None,
        type: Optional[RUN_TYPE_LITERAL] = None
    ) -> List[RunBase]:
        query = select(run).where(run.c.user_id == user_id)

        if run_id:
            query = query.where(run.c.id == run_id)
        if run_ids:
            query = query.where(run.c.id.in_(run_ids))
        if project_id:
            query = query.where(run.c.project_id == project_id)
        if status:
            query = query.where(run.c.status == status)
        if filter_status:
            query = query.where(run.c.status.in_(filter_status))
        if type:
            query = query.where(run.c.type == type)

        query = query.order_by(run.c.started_at.desc())

        records = await fetch_all(query)

        return [RunBase(**record) for record in records]

    async def get_run_messages(
        self,
        run_id: uuid.UUID,
        type: Optional[Literal["tool_call", "result", "error"]] = None
    ) -> List[RunMessageBase]:
        query = select(run_message).where(run_message.c.run_id == run_id)

        if type:
            query = query.where(run_message.c.type == type)

        query = query.order_by(run_message.c.created_at)

        records = await fetch_all(query)

        return [RunMessageBase(**record) for record in records]

    async def create_run_message(self, create: RunMessageCreate) -> RunMessageBase:
        # Infer agent from run type
        runs = await self.get_runs(run_ids=[create.run_id])
        if not runs:
            raise ValueError(f"Run with id {create.run_id} not found")
        run_type = runs[0].type

        run_message_obj = RunMessageBase(
            id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            run_id=create.run_id,
            content=create.content,
            type=create.type,
            agent=run_type
        )

        await execute(insert(run_message).values(**run_message_obj.model_dump()), commit_after=True)

        return run_message_obj

    async def update_run_name(self, run_id: uuid.UUID, name: str) -> RunBase:
        await execute(
            update(run)
            .where(run.c.id == run_id)
            .values(run_name=name),
            commit_after=True
        )

        runs = await self.get_runs(run_ids=[run_id])
        return runs[0]

    async def create_run(self, user_id: uuid.UUID, create: RunCreate) -> RunBase:
        return await self._create_run(user_id, create)


@v1_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    state.callbacks = ApplicationCallbacks()
