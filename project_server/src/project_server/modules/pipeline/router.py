from fastapi import APIRouter
from project_server.modules.pipeline.schema import RunPipelineRequest, FunctionCreate, PipelineCreate

router = APIRouter()


# TODO: Add auth


@router.post("/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):
    pass


@router.post("/pipeline")
async def create_pipeline(request: PipelineCreate):
    pass


@router.post("/function")
async def create_function(request: FunctionCreate):
    pass
