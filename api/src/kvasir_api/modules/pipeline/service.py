import uuid
from datetime import datetime, timezone
from typing import List, Optional, Annotated
from sqlalchemy import select, insert, delete
from fastapi import HTTPException, Depends

from kvasir_api.auth.service import get_current_user
from kvasir_api.auth.schema import User
from kvasir_api.database.service import fetch_all, execute
from kvasir_api.modules.pipeline.models import (
    pipeline,
    pipeline_implementation,
    pipeline_run,
)
from kvasir_api.modules.kvasir_v1.models import swe_run
from kvasir_ontology.entities.pipeline.data_model import (
    PipelineBase,
    PipelineImplementationBase,
    Pipeline,
    PipelineCreate,
    PipelineImplementationCreate,
    PipelineRunBase,
    PipelineRunCreate,
    PIPELINE_RUN_STATUS_LITERAL
)
from kvasir_ontology.entities.pipeline.interface import PipelineInterface


class Pipelines(PipelineInterface):

    async def create_pipeline(self, pipeline_create: PipelineCreate) -> Pipeline:
        pipeline_record = PipelineBase(
            id=uuid.uuid4(),
            user_id=self.user_id,
            **pipeline_create.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(pipeline).values(pipeline_record.model_dump()), commit_after=True)

        implementation_obj = None
        if pipeline_create.implementation_create:
            implementation_obj = await self.create_pipeline_implementation(pipeline_create.implementation_create)

        runs_objs = []
        if pipeline_create.runs_create:
            runs_objs = await self.create_pipeline_runs(pipeline_create.runs_create)

        return Pipeline(
            **pipeline_record.model_dump(),
            runs=runs_objs,
            implementation=implementation_obj
        )

    async def create_pipeline_implementation(self, pipeline_implementation_create: PipelineImplementationCreate) -> Pipeline:
        pipeline_record = await self.get_pipeline(pipeline_implementation_create.pipeline_id)
        if not pipeline_record:
            raise HTTPException(
                status_code=404, detail=f"Pipeline with id {pipeline_implementation_create.pipeline_id} not found")

        pipeline_implementation_obj = PipelineImplementationBase(
            id=pipeline_record.id,
            **pipeline_implementation_create.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(pipeline_implementation).values(**pipeline_implementation_obj.model_dump()), commit_after=True)

        # Return the full Pipeline with the newly created implementation
        return await self.get_pipeline(pipeline_implementation_create.pipeline_id)

    async def create_pipeline_run(self, pipeline_run_create: PipelineRunCreate) -> PipelineRunBase:
        return (await self.create_pipeline_runs([pipeline_run_create]))[0]

    async def create_pipeline_runs(self, pipeline_runs_create: List[PipelineRunCreate]) -> List[PipelineRunBase]:
        pipeline_runs_objs = [
            PipelineRunBase(
                id=uuid.uuid4(),
                **pipeline_run_create.model_dump(),
                start_time=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ) for pipeline_run_create in pipeline_runs_create
        ]
        await execute(insert(pipeline_run).values([run.model_dump() for run in pipeline_runs_objs]), commit_after=True)
        return pipeline_runs_objs

    async def get_pipeline(self, pipeline_id: uuid.UUID) -> Pipeline:
        return (await self.get_pipelines([pipeline_id]))[0]

    async def get_pipelines(self, pipeline_ids: Optional[List[uuid.UUID]] = None) -> List[Pipeline]:

        pipeline_query = select(pipeline).where(
            pipeline.c.user_id == self.user_id)
        if pipeline_ids is not None:
            pipeline_query = pipeline_query.where(
                pipeline.c.id.in_(pipeline_ids))

        pipelines = await fetch_all(pipeline_query)

        if not pipelines:
            return []

        pipeline_ids = [p["id"] for p in pipelines]

        pipeline_implementation_query = select(pipeline_implementation).where(
            pipeline_implementation.c.id.in_(pipeline_ids))

        pipeline_implementations = await fetch_all(pipeline_implementation_query)

        # pipeline runs
        pipeline_runs_query = select(pipeline_run).where(
            pipeline_run.c.pipeline_id.in_(pipeline_ids))
        pipeline_runs = await fetch_all(pipeline_runs_query)

        output_objs = []
        for pipe_id in pipeline_ids:
            pipe_obj = PipelineBase(**next(
                iter([p for p in pipelines if p["id"] == pipe_id])))

            pipe_implementation_record = next(iter([
                p for p in pipeline_implementations if p["id"] == pipe_id]), None)

            pipeline_implementation_obj = None
            if pipe_implementation_record:

                pipeline_implementation_obj = PipelineImplementationBase(
                    **pipe_implementation_record)

            runs_objs = []
            runs_records = [
                r for r in pipeline_runs if r["pipeline_id"] == pipe_id]

            for run_record in runs_records:
                runs_objs.append(PipelineRunBase(**run_record))

            output_objs.append(Pipeline(
                **pipe_obj.model_dump(),
                runs=runs_objs,
                implementation=pipeline_implementation_obj
            ))

        return output_objs

    async def get_pipeline_runs(
        self,
        only_running: bool = False,
        pipeline_ids: Optional[List[uuid.UUID]] = None,
        run_ids: Optional[List[uuid.UUID]] = None
    ) -> List[PipelineRunBase]:

        pipeline_runs_query = select(pipeline_run
                                     ).join(pipeline, pipeline_run.c.pipeline_id == pipeline.c.id
                                            ).where(pipeline.c.user_id == self.user_id)

        if pipeline_ids is not None:
            pipeline_runs_query = pipeline_runs_query.where(
                pipeline_run.c.pipeline_id.in_(pipeline_ids))
        if run_ids is not None:
            pipeline_runs_query = pipeline_runs_query.where(
                pipeline_run.c.id.in_(run_ids))
        if only_running:
            pipeline_runs_query = pipeline_runs_query.where(
                pipeline_run.c.status == "running")

        pipeline_runs = await fetch_all(pipeline_runs_query)

        if not pipeline_runs:
            return []

        result = []
        for run in pipeline_runs:
            result.append(PipelineRunBase(**run))

        return result

    async def get_pipeline_run(self, pipeline_run_id: uuid.UUID) -> PipelineRunBase:
        runs = await self.get_pipeline_runs(run_ids=[pipeline_run_id])
        if not runs:
            raise HTTPException(
                status_code=404, detail=f"Pipeline run with id {pipeline_run_id} not found")
        return runs[0]

    async def update_pipeline_run_status(self, pipeline_run_id: uuid.UUID, status: PIPELINE_RUN_STATUS_LITERAL) -> PipelineRunBase:
        await execute(
            pipeline_run.update().where(pipeline_run.c.id == pipeline_run_id).values(
                status=status,
                updated_at=datetime.now(timezone.utc)
            ),
            commit_after=True
        )
        return (await self.get_pipeline_run(pipeline_run_id))

    async def delete_pipeline(self, pipeline_id: uuid.UUID) -> None:
        await execute(delete(swe_run).where(swe_run.c.pipeline_id == pipeline_id), commit_after=True)
        await execute(delete(pipeline_run).where(pipeline_run.c.pipeline_id == pipeline_id), commit_after=True)
        await execute(delete(pipeline_implementation).where(pipeline_implementation.c.id == pipeline_id), commit_after=True)
        await execute(delete(pipeline).where(pipeline.c.id == pipeline_id), commit_after=True)


# For dependency injection
async def get_pipelines_service(user: Annotated[User, Depends(get_current_user)]) -> PipelineInterface:
    return Pipelines(user.id)
