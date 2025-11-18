import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from typing import List, Annotated
from uuid import UUID

from synesis_api.auth.service import get_current_user, user_owns_pipeline, user_owns_pipeline_run
from synesis_api.auth.schema import User
from synesis_api.modules.pipeline.service import get_pipelines_service
from kvasir_ontology.entities.pipeline.interface import PipelineInterface
from kvasir_ontology.entities.pipeline.data_model import (
    Pipeline,
    PipelineImplementationCreate,
    PipelineRunBase,
    PipelineRunCreate,
    PipelineCreate,
    PIPELINE_RUN_STATUS_LITERAL
)
from synesis_api.app_secrets import SSE_MIN_SLEEP_TIME

router = APIRouter()


@router.get("/pipelines/runs", response_model=List[PipelineRunBase])
async def fetch_pipeline_runs(
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> List[PipelineRunBase]:
    return await pipeline_service.get_pipeline_runs()


@router.get("/pipelines/{pipeline_id}", response_model=Pipeline)
async def fetch_pipeline(
    pipeline_id: UUID,
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> Pipeline:
    return await pipeline_service.get_pipeline(pipeline_id)


@router.get("/pipelines-by-ids", response_model=List[Pipeline])
async def fetch_pipelines_by_ids(
    pipeline_ids: List[UUID],
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> List[Pipeline]:
    """Get pipelines by IDs"""
    return await pipeline_service.get_pipelines(pipeline_ids)


@router.post("/pipeline", response_model=Pipeline)
async def post_pipeline(
    request: PipelineCreate,
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> Pipeline:
    return await pipeline_service.create_pipeline(request)


@router.post("/pipeline-implementation", response_model=Pipeline)
async def post_pipeline_implementation(
    request: PipelineImplementationCreate,
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> Pipeline:
    pipeline = await pipeline_service.create_pipeline_implementation(request)
    return pipeline


@router.post("/pipeline-run", response_model=PipelineRunBase)
async def post_pipeline_run(
    request: PipelineRunCreate,
    user: Annotated[User, Depends(get_current_user)],
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> PipelineRunBase:

    if not await user_owns_pipeline(user.id, request.pipeline_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to run this pipeline")

    return await pipeline_service.create_pipeline_run(request)


@router.patch("/pipelines/{pipeline_run_id}/status", response_model=PipelineRunBase)
async def patch_pipeline_run_status(
    pipeline_run_id: UUID,
    status: PIPELINE_RUN_STATUS_LITERAL,
    user: Annotated[User, Depends(get_current_user)],
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> PipelineRunBase:

    if not await user_owns_pipeline_run(user.id, str(pipeline_run_id)):
        raise HTTPException(
            status_code=403, detail="You do not have permission to update the status of this pipeline run")

    pipeline_run = await pipeline_service.update_pipeline_run_status(pipeline_run_id, status)
    return pipeline_run


@router.get("/stream-pipeline-runs")
async def stream_pipeline_runs(
    pipeline_service: Annotated[PipelineInterface,
                                Depends(get_pipelines_service)]
) -> StreamingResponse:
    adapter = TypeAdapter(List[PipelineRunBase])

    async def stream_incomplete_runs():
        prev_run_ids = []
        while True:
            incomplete_runs = await pipeline_service.get_pipeline_runs(only_running=True)

            # Include recently stopped runs to ensure we don't miss the associated state changes
            # Could optionally listen for when a run id is removed from this list in the frontend, then mutate all jobs, but this is more efficient
            stopped_run_ids = [
                run_id for run_id in prev_run_ids if run_id not in [run.id for run in incomplete_runs]]
            stopped_runs = await pipeline_service.get_pipeline_runs(run_ids=stopped_run_ids)

            runs = stopped_runs + incomplete_runs
            yield f"data: {adapter.dump_json(runs, by_alias=True).decode('utf-8')}\n\n"
            prev_run_ids = [run.id for run in runs]

            await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")
