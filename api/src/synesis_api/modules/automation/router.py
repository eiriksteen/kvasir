import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from synesis_api.modules.automation.schema import ModelComplete
from synesis_api.modules.automation.service import (
    get_model_complete,
    get_all_models_public_or_owned,
    get_user_models,
    user_owns_model,
    model_is_public
)
from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user

router = APIRouter()


@router.get("/models", response_model=List[ModelComplete])
async def get_all_models(
    user: Annotated[User, Depends(get_current_user)] = None,
    include_integration_jobs: bool = False
) -> List[ModelComplete]:
    """Get all automation models with joined data"""
    try:
        return await get_all_models_public_or_owned(user.id, include_integration_jobs=include_integration_jobs)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.get("/models/my", response_model=List[ModelComplete])
async def get_my_models(
    user: Annotated[User, Depends(get_current_user)] = None,
    include_integration_jobs: bool = False
) -> List[ModelComplete]:
    """Get all automation models owned by the current user"""
    try:
        results = await get_user_models(user.id, include_integration_jobs=include_integration_jobs)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user models: {str(e)}"
        )


@router.get("/models/{model_id}", response_model=ModelComplete)
async def get_model(
    model_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    include_integration_jobs: bool = False
) -> ModelComplete:
    """Get a specific automation model with joined data by ID"""

    if not await user_owns_model(user.id, model_id) and not await model_is_public(model_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this model"
        )

    try:
        return await get_model_complete(model_id, include_integration_jobs=include_integration_jobs)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model: {str(e)}"
        )
