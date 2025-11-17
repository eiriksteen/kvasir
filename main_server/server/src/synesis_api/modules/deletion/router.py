from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user
from synesis_api.modules.project.service import (
    delete_data_source_from_project,
    delete_dataset_from_project,
    delete_model_entity_from_project,
    delete_pipeline_from_project,
    delete_analysis_from_project,
)


router = APIRouter()


@router.delete("/data-source/{data_source_id}")
async def delete_data_source_endpoint(
    data_source_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """Delete a data source and remove it from all projects."""
    deleted_id = await delete_data_source_from_project(user.id, data_source_id)
    return {"message": "Data source deleted successfully", "id": str(deleted_id)}


@router.delete("/dataset/{dataset_id}")
async def delete_dataset_endpoint(
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """Delete a dataset and remove it from all projects."""
    deleted_id = await delete_dataset_from_project(user.id, dataset_id)
    return {"message": "Dataset deleted successfully", "id": str(deleted_id)}


@router.delete("/model-instantiated/{model_instantiated_id}")
async def delete_model_entity_endpoint(
    model_instantiated_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """Delete a model entity and remove it from all projects."""
    deleted_id = await delete_model_entity_from_project(user.id, model_instantiated_id)
    return {"message": "Model entity deleted successfully", "id": str(deleted_id)}


@router.delete("/pipeline/{pipeline_id}")
async def delete_pipeline_endpoint(
    pipeline_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """Delete a pipeline and remove it from all projects."""
    deleted_id = await delete_pipeline_from_project(user.id, pipeline_id)
    return {"message": "Pipeline deleted successfully", "id": str(deleted_id)}


@router.delete("/analysis/{analysis_id}")
async def delete_analysis_endpoint(
    analysis_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> dict:
    """Delete an analysis and remove it from all projects."""
    deleted_id = await delete_analysis_from_project(user.id, analysis_id)
    return {"message": "Analysis deleted successfully", "id": str(deleted_id)}
