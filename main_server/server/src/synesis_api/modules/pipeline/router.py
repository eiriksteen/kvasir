from fastapi import APIRouter, Depends

from synesis_api.auth.service import get_current_user
from synesis_schemas.main_server import User
from synesis_api.modules.pipeline.service import get_user_pipelines, get_user_pipeline_with_functions, create_pipeline
from synesis_schemas.main_server import PipelineFull, PipelineCreate, FunctionCreate, FunctionInDB, PipelineInDB
from synesis_api.modules.pipeline.service import create_function

router = APIRouter()


@router.get("/user-pipelines")
async def fetch_pipelines(user: User = Depends(get_current_user),):
    pipelines = await get_user_pipelines(user.id)

    return pipelines


@router.get("/user-pipeline/{pipeline_id}")
async def fetch_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
) -> PipelineFull:

    pipe = await get_user_pipeline_with_functions(user.id, pipeline_id)

    return pipe


@router.post("/pipeline", response_model=PipelineInDB)
async def post_pipeline(
    request: PipelineCreate,
    user: User = Depends(get_current_user),
) -> PipelineInDB:

    pipeline = await create_pipeline(
        request.name,
        request.description,
        user.id,
        request.function_ids,
        request.function_configs,
        request.periodic_schedules,
        request.on_event_schedules
    )

    return pipeline


@router.post("/function", response_model=FunctionInDB)
async def post_function(
    request: FunctionCreate,
    user: User = Depends(get_current_user),
) -> FunctionInDB:

    function = await create_function(
        request.name,
        request.description,
        request.implementation_script,
        user.id,
        request.inputs,
        request.outputs,
        request.setup_script,
        request.config_dict
    )

    return function
