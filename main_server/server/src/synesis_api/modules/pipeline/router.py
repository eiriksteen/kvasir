import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from typing import List
from uuid import UUID

from synesis_api.auth.service import get_current_user, user_owns_pipeline, user_owns_pipeline_run, oauth2_scheme
from synesis_schemas.main_server import User
from synesis_api.modules.pipeline.service import (
    create_pipeline,
    create_pipeline_implementation,
    get_pipeline_runs,
    create_pipeline_run,
    update_pipeline_run_status,
    create_pipeline_output_model_entity,
    create_pipeline_output_dataset,
    get_user_pipelines
)
from synesis_api.client import MainServerClient, post_run_pipeline
from synesis_schemas.project_server import RunPipelineRequest
from synesis_schemas.main_server import (
    Pipeline,
    PipelineImplementationCreate,
    PipelineInDB,
    PipelineRunInDB,
    PipelineOutputModelEntityInDB,
    PipelineOutputDatasetInDB,
    PipelineRunStatusUpdate,
    PipelineRunDatasetOutputCreate,
    PipelineRunModelEntityOutputCreate,
    PipelineCreate,
    PipelineImplementationInDB
)
from synesis_api.app_secrets import SSE_MIN_SLEEP_TIME

router = APIRouter()


@router.get("/pipelines/runs", response_model=List[PipelineRunInDB])
async def fetch_pipeline_runs(user: User = Depends(get_current_user)) -> List[PipelineRunInDB]:
    return await get_pipeline_runs(user.id)


@router.get("/pipelines/{pipeline_id}", response_model=Pipeline)
async def fetch_pipeline(
    pipeline_id: UUID,
    user: User = Depends(get_current_user),
) -> Pipeline:
    return (await get_user_pipelines(user.id, [pipeline_id]))[0]


@router.post("/pipeline", response_model=PipelineInDB)
async def post_pipeline(
    request: PipelineCreate,
    user: User = Depends(get_current_user),
) -> PipelineInDB:
    return await create_pipeline(user.id, request)


@router.post("/pipeline-implementation", response_model=PipelineImplementationInDB)
async def post_pipeline_implementation(
    request: PipelineImplementationCreate,
    user: User = Depends(get_current_user),
) -> PipelineImplementationInDB:
    pipeline = await create_pipeline_implementation(user.id, request)
    return pipeline


@router.post("/run-pipeline", response_model=PipelineInDB)
async def run_pipeline(
    request: RunPipelineRequest,
    user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
) -> PipelineInDB:

    if not await user_owns_pipeline(user.id, request.pipeline_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to run this pipeline")

    await post_run_pipeline(MainServerClient(token), request)

    return (await get_user_pipelines(user.id, [request.pipeline_id]))[0]


@router.post("/pipelines/{pipeline_id}/run-object", response_model=PipelineRunInDB)
async def post_pipeline_run_object(
    pipeline_id: str,
    user: User = Depends(get_current_user),
) -> PipelineRunInDB:

    if not await user_owns_pipeline(user.id, pipeline_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to run this pipeline")

    pipeline = await create_pipeline_run(pipeline_id)
    return pipeline


@router.patch("/pipelines/{pipeline_run_id}/status", response_model=PipelineRunInDB)
async def patch_pipeline_run_status(
    pipeline_run_id: str,
    request: PipelineRunStatusUpdate,
    user: User = Depends(get_current_user),
) -> PipelineRunInDB:

    if not await user_owns_pipeline_run(user.id, pipeline_run_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to update the status of this pipeline run")

    pipeline = await update_pipeline_run_status(pipeline_run_id, request.status)
    return pipeline


@router.get("/stream-pipeline-runs")
async def stream_pipeline_runs(user: User = Depends(get_current_user),) -> StreamingResponse:
    adapter = TypeAdapter(List[PipelineRunInDB])

    async def stream_incomplete_runs():
        prev_run_ids = []
        while True:
            incomplete_runs = await get_pipeline_runs(user.id, only_running=True)

            # Include recently stopped runs to ensure we don't miss the associated state changes
            # Could optionally listen for when a run id is removed from this list in the frontend, then mutate all jobs, but this is more efficient
            stopped_run_ids = [
                run_id for run_id in prev_run_ids if run_id not in [run.id for run in incomplete_runs]]
            stopped_runs = await get_pipeline_runs(user.id, run_ids=stopped_run_ids)

            runs = stopped_runs + incomplete_runs
            yield f"data: {adapter.dump_json(runs, by_alias=True).decode("utf-8")}\n\n"
            prev_run_ids = [run.id for run in runs]

            await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_incomplete_runs(), media_type="text/event-stream")


@router.post("/pipelines/{pipeline_id}/output-model-entity", response_model=PipelineOutputModelEntityInDB)
async def post_output_model_entity(
    pipeline_id: str,
    request: PipelineRunModelEntityOutputCreate,
    user: User = Depends(get_current_user)
) -> PipelineOutputModelEntityInDB:
    if not await user_owns_pipeline(user.id, pipeline_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to output a model entity to this pipeline")

    return await create_pipeline_output_model_entity(pipeline_id, request)


@router.post("/pipelines/{pipeline_id}/output-dataset", response_model=PipelineOutputDatasetInDB)
async def post_output_dataset(
    pipeline_id: str,
    request: PipelineRunDatasetOutputCreate,
    user: User = Depends(get_current_user)
) -> PipelineOutputDatasetInDB:
    if not await user_owns_pipeline(user.id, pipeline_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to output a dataset to this pipeline")

    return await create_pipeline_output_dataset(pipeline_id, request)
