import json
import uuid
from uuid import UUID
from typing import Literal, List, Dict, Optional
from datetime import datetime, timezone
from pydantic_ai.models import ModelMessage
from taskiq import TaskiqState, TaskiqEvents
from pydantic_ai.messages import ModelMessagesTypeAdapter
from sqlalchemy import insert, select, delete, update, and_

from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.kvasir_v1.models import (
    run,
    swe_run,
    analysis_run,
    result,
    message,
    results_queue,
    deps,
    pydantic_ai_message
)
from synesis_api.modules.ontology.service import create_ontology_for_user
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.broker import logger, v1_broker
from kvasir_research.agents.v1.data_model import (
    AnalysisRun,
    SweRun,
    RunBase,
    RunCreate,
    MessageCreate,
    Message,
    ResultsQueue,
    DepsBase,
    ResultBase,
    PydanticAIMessage,
    RUN_TYPE_LITERAL,
    RESULT_TYPE_LITERAL,
    MESSAGE_TYPE_LITERAL
)

from kvasir_ontology.ontology import Ontology


class ApplicationCallbacks(KvasirV1Callbacks):

    async def _verify_run_ownership(self, user_id: UUID, run_id: UUID) -> None:
        query = select(run).where(
            and_(run.c.id == run_id, run.c.user_id == user_id))
        record = await fetch_one(query)
        if not record:
            raise ValueError(
                f"Run with id {run_id} not found or does not belong to user {user_id}")

    def create_ontology(self, user_id: UUID, mount_group_id: UUID, bearer_token: str | None = None) -> Ontology:
        return create_ontology_for_user(user_id, mount_group_id, bearer_token)

    async def get_run_status(self, user_id: UUID, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        query = select(run).where(
            and_(run.c.id == run_id, run.c.user_id == user_id))
        record = await fetch_one(query)
        if not record:
            raise ValueError(f"Run with id {run_id} not found")
        return RunBase(**record).status

    async def set_run_status(self, user_id: UUID, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        await execute(
            update(run)
            .where(and_(run.c.id == run_id, run.c.user_id == user_id))
            .values(status=status),
            commit_after=True
        )
        return status

    async def create_swe_run(self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, pipeline_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> SweRun:
        run_create = RunCreate(
            type="swe",
            run_name=run_name or "swe run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self.create_run(user_id, run_create)

        await execute(
            insert(swe_run).values(
                run_id=run_record.id,
                pipeline_id=pipeline_id,
                kvasir_run_id=kvasir_run_id,
                created_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

        return SweRun(
            **run_record.model_dump(),
            kvasir_run_id=kvasir_run_id,
            pipeline_id=pipeline_id,
            result=None
        )

    async def create_analysis_run(self, user_id: UUID, project_id: UUID, kvasir_run_id: UUID, analysis_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> AnalysisRun:
        run_create = RunCreate(
            type="analysis",
            run_name=run_name or "analysis run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self.create_run(user_id, run_create)

        await execute(
            insert(analysis_run).values(
                run_id=run_record.id,
                analysis_id=analysis_id,
                kvasir_run_id=kvasir_run_id,
                created_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )

        return AnalysisRun(
            **run_record.model_dump(),
            analysis_id=analysis_id,
            kvasir_run_id=kvasir_run_id,
            result=None
        )

    async def create_kvasir_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> RunBase:
        run_create = RunCreate(
            type="kvasir",
            run_name=run_name or "kvasir run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self.create_run(user_id, run_create)
        return run_record

    async def create_extraction_run(self, user_id: UUID, project_id: UUID, run_name: str | None = None, initial_status: Literal["pending", "completed", "failed", "waiting", "running"] | None = None) -> RunBase:
        run_create = RunCreate(
            type="extraction",
            run_name=run_name or "extraction run",
            initial_status=initial_status or "running",
            project_id=project_id,
        )
        run_record = await self.create_run(user_id, run_create)
        return run_record

    async def _get_latest_results_queue_item(self, user_id: UUID, run_id: UUID) -> Optional[ResultsQueue]:
        await self._verify_run_ownership(user_id, run_id)
        query = select(results_queue).where(results_queue.c.run_id == run_id).order_by(
            results_queue.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return ResultsQueue(**record)
        return None

    async def get_results_queue(self, user_id: UUID, run_id: UUID) -> List[str]:
        queue_item = await self._get_latest_results_queue_item(user_id, run_id)
        if queue_item:
            return queue_item.content
        return []

    async def pop_result_from_queue(self, user_id: UUID, run_id: UUID) -> str:
        queue_item = await self._get_latest_results_queue_item(user_id, run_id)
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

    async def add_result_to_queue(self, user_id: UUID, run_id: UUID, result: str) -> None:
        await self._verify_run_ownership(user_id, run_id)
        queue_item = await self._get_latest_results_queue_item(user_id, run_id)
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

    async def _get_latest_deps(self, user_id: UUID, run_id: UUID, type: Optional[RUN_TYPE_LITERAL] = None) -> Optional[DepsBase]:
        await self._verify_run_ownership(user_id, run_id)
        query = select(deps).where(deps.c.run_id == run_id)
        if type:
            query = query.where(deps.c.type == type)
        query = query.order_by(deps.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return DepsBase(**record)
        return None

    async def save_deps(self, user_id: UUID, run_id: UUID, deps_dict: Dict) -> None:
        await self._verify_run_ownership(user_id, run_id)
        run_record = await fetch_one(select(run).where(run.c.id == run_id))
        run_type = RunBase(**run_record).type
        deps_obj = DepsBase(
            id=uuid.uuid4(),
            run_id=run_id,
            type=run_type,
            content=json.dumps(deps_dict),
            created_at=datetime.now(timezone.utc)
        )
        await execute(insert(deps).values(**deps_obj.model_dump()), commit_after=True)

    async def load_deps(self, user_id: UUID, run_id: UUID) -> Dict:
        deps_obj = await self._get_latest_deps(user_id, run_id)
        if deps_obj:
            return json.loads(deps_obj.content)
        return {}

    async def _get_latest_result(self, user_id: UUID, run_id: UUID, type: Optional[RESULT_TYPE_LITERAL] = None) -> Optional[ResultBase]:
        await self._verify_run_ownership(user_id, run_id)
        query = select(result).where(result.c.run_id == run_id)
        if type:
            query = query.where(result.c.type == type)
        query = query.order_by(result.c.created_at.desc()).limit(1)
        record = await fetch_one(query)
        if record:
            return ResultBase(**record)
        return None

    async def save_result(self, user_id: UUID, run_id: UUID, result_content: str, type: Literal["swe", "analysis", "kvasir"]) -> None:
        await self._verify_run_ownership(user_id, run_id)
        result_obj = ResultBase(
            id=uuid.uuid4(),
            run_id=run_id,
            type=type,
            content=result_content,
            created_at=datetime.now(timezone.utc)
        )
        await execute(insert(result).values(**result_obj.model_dump()), commit_after=True)

    async def get_result(self, user_id: UUID, run_id: UUID, type: Literal["swe", "analysis", "kvasir"]) -> str:
        result_obj = await self._get_latest_result(user_id, run_id, type=type)
        if result_obj:
            return result_obj.content
        raise ValueError(f"No {type} result found for run_id {run_id}")

    async def get_analysis_run(self, user_id: UUID, run_id: UUID) -> AnalysisRun:
        query = select(
            run,
            analysis_run.c.analysis_id,
            analysis_run.c.kvasir_run_id
        ).select_from(
            analysis_run.join(run, analysis_run.c.run_id == run.c.id)
        ).where(and_(run.c.id == run_id, run.c.user_id == user_id))

        record = await fetch_one(query)
        if not record:
            raise ValueError(
                f"Analysis run with run_id {run_id} not found or does not belong to user {user_id}")

        run_base = RunBase(**record)

        result_obj = await self._get_latest_result(user_id, run_base.id, type="analysis")

        return AnalysisRun(
            **run_base.model_dump(),
            analysis_id=record["analysis_id"],
            kvasir_run_id=record["kvasir_run_id"],
            result=result_obj
        )

    async def get_swe_run(self, user_id: UUID, run_id: UUID) -> SweRun:
        query = select(
            run,
            swe_run.c.kvasir_run_id
        ).select_from(
            swe_run.join(run, swe_run.c.run_id == run.c.id)
        ).where(and_(run.c.id == run_id, run.c.user_id == user_id))

        record = await fetch_one(query)
        if not record:
            raise ValueError(
                f"SWE run with id {run_id} not found or does not belong to user {user_id}")

        run_base = RunBase(**record)

        result_obj = await self._get_latest_result(user_id, run_base.id, type="swe")

        return SweRun(
            **run_base.model_dump(),
            kvasir_run_id=record["kvasir_run_id"],
            result=result_obj
        )

    async def save_message_history(self, user_id: UUID, run_id: UUID, message_history: List[ModelMessage]) -> None:
        await self._verify_run_ownership(user_id, run_id)
        message_bytes = ModelMessagesTypeAdapter.dump_json(message_history)
        pydantic_ai_message_records = [PydanticAIMessage(
            id=uuid.uuid4(),
            run_id=run_id,
            message_list=message_bytes,
            created_at=datetime.now(timezone.utc)
        )]
        await execute(insert(pydantic_ai_message).values([record.model_dump() for record in pydantic_ai_message_records]), commit_after=True)

    async def get_message_history(self, user_id: UUID, run_id: UUID) -> List[ModelMessage] | None:
        await self._verify_run_ownership(user_id, run_id)
        c = await fetch_all(
            select(pydantic_ai_message).where(
                pydantic_ai_message.c.run_id == run_id)
        )
        messages: list[ModelMessage] = []
        for message in c:
            messages.extend(
                ModelMessagesTypeAdapter.validate_json(message["message_list"]))
        return messages if messages else None

    async def log(self, user_id: UUID, run_id: UUID, message: str, type: Literal["result", "tool_call", "error", "info"]) -> None:
        log_message = f"[{run_id}] [{type.upper()}] {message}"
        logger.info(log_message)
        # Infer role from run type
        runs = await self.get_runs(user_id=user_id, run_ids=[run_id])
        if not runs:
            raise ValueError(f"Run with id {run_id} not found")
        role = runs[0].type

        await self.create_message(user_id, MessageCreate(
            run_id=run_id,
            content=message,
            type=type,
            role=role
        ))

    async def get_runs(
        self,
        user_id: UUID,
        run_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        filter_status: Optional[List[str]] = None,
        type: Optional[RUN_TYPE_LITERAL] = None
    ) -> List[RunBase]:
        query = select(run).where(run.c.user_id == user_id)

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

        if not records:
            return []

        run_id_list = [record["id"] for record in records]

        analysis_run_query = select(
            analysis_run.c.run_id,
            analysis_run.c.analysis_id,
            analysis_run.c.kvasir_run_id
        ).where(analysis_run.c.run_id.in_(run_id_list))
        analysis_run_records = await fetch_all(analysis_run_query)
        analysis_run_map = {record["run_id"]
            : record for record in analysis_run_records}

        swe_run_query = select(swe_run).where(
            swe_run.c.run_id.in_(run_id_list))
        swe_run_records = await fetch_all(swe_run_query)
        swe_run_map = {record["run_id"]: record for record in swe_run_records}

        run_results_query = select(result).where(
            result.c.run_id.in_(run_id_list))
        run_results_records = await fetch_all(run_results_query)
        run_results_map = {record["run_id"]
            : record for record in run_results_records}

        result_objs = []
        for record in records:
            run_base = RunBase(**record)
            run_id = run_base.id

            if run_id in analysis_run_map:
                analysis_run_data = analysis_run_map[run_id]
                result_obj = run_results_map.get(run_id, None)
                result_objs.append(AnalysisRun(
                    **run_base.model_dump(),
                    analysis_id=analysis_run_data["analysis_id"],
                    kvasir_run_id=analysis_run_data["kvasir_run_id"],
                    result=result_obj
                ))
            elif run_id in swe_run_map:
                swe_run_data = swe_run_map[run_id]
                result_obj = run_results_map.get(run_id, None)
                result_objs.append(SweRun(
                    **run_base.model_dump(),
                    kvasir_run_id=swe_run_data["kvasir_run_id"],
                    pipeline_id=swe_run_data["pipeline_id"],
                    result=result_obj,
                ))
            else:
                result_objs.append(run_base)

        return result_objs

    async def get_messages(
        self,
        user_id: UUID,
        run_id: UUID,
        types: Optional[List[MESSAGE_TYPE_LITERAL]] = None
    ) -> List[Message]:
        await self._verify_run_ownership(user_id, run_id)
        query = select(message).where(message.c.run_id == run_id)

        if types:
            query = query.where(message.c.type.in_(types))

        query = query.order_by(message.c.created_at)

        records = await fetch_all(query)

        return [Message(**record) for record in records]

    async def create_message(self, user_id: UUID, message_create: MessageCreate) -> Message:
        await self._verify_run_ownership(user_id, message_create.run_id)
        message_obj = Message(
            id=uuid.uuid4(),
            created_at=datetime.now(timezone.utc),
            **message_create.model_dump()
        )

        await execute(insert(message).values(**message_obj.model_dump()), commit_after=True)

        return message_obj

    async def update_run_name(self, user_id: UUID, run_id: UUID, name: str) -> RunBase:
        await self._verify_run_ownership(user_id, run_id)
        await execute(
            update(run)
            .where(and_(run.c.id == run_id, run.c.user_id == user_id))
            .values(run_name=name),
            commit_after=True
        )

        runs = await self.get_runs(user_id=user_id, run_ids=[run_id])
        return runs[0]

    async def create_run(self, user_id: UUID, create: RunCreate) -> RunBase:
        create_dict = create.model_dump(exclude={"initial_status"})
        run_obj = RunBase(
            id=uuid.uuid4(),
            user_id=user_id,
            status=create.initial_status,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            **create_dict
        )
        await execute(insert(run).values(**run_obj.model_dump()), commit_after=True)
        return run_obj


@v1_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    state.callbacks = ApplicationCallbacks()
