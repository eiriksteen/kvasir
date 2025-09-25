from fastapi import APIRouter
from synesis_schemas.project_server import RunPipelineRequest, FunctionCreate, PipelineCreate

router = APIRouter()


# TODO: Add auth


@router.post("/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):

    # Run the pipeline and create a new enitity in the frontend for the results
    pass


@router.post("/pipeline")
async def create_pipeline(request: PipelineCreate):
    pass


@router.post("/function")
async def create_function(request: FunctionCreate):
    pass
