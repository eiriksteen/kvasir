import uuid
import aiofiles
import pandas as pd
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from io import StringIO
from pathlib import Path
from .schema import ModelJobMetadata, ModelJobResult
from .service import (get_job_metadata,
                      get_job_results,
                      create_model_job,
                      run_model_agent,
                      run_model_job)
from ..auth.schema import User
from ..auth.service import (create_api_key,
                            get_current_user,
                            get_user_from_api_key,
                            delete_api_key,
                            user_owns_model_job)
# from ..project_spec.schema import ChatSummary

router = APIRouter()

@router.post("/call-model-agent", response_model=ModelJobMetadata)
async def call_model_agent(
    # project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelJobMetadata:
    # project_description = ChatSummary()
    try:
        async with aiofiles.open("files/98ca0ae7-5221-4ec0-9bf3-092a0445695a/c93e686e-f16d-4329-8882-0adce1218126.html", mode='r', encoding='utf-8') as file:
            data_analysis = await file.read()
    except:
        raise HTTPException(status_code=404, detail="Could not find data analysis.")

    try:
        api_key = await create_api_key(user)
        model_job = await create_model_job(user.id, api_key.id)
    except:
        raise HTTPException(status_code=500, detail="Failed to create model job.")
    
    data_dir = Path("files") / "98ca0ae7-5221-4ec0-9bf3-092a0445695a"
    data_path = data_dir / "0b1626e1-d671-47ad-9013-f6ea23b35763.csv"
    project_description = "The goal of this project is to analyze and model the Boston Housing Dataset, with the aim of predicting house prices based on various features. This dataset contains information about different attributes of houses in the Boston area, such as crime rates, average number of rooms, and proximity to employment centers. The project explores the relationship between these attributes and the price of homes, allowing for both descriptive and predictive analytics."

    try:
        model = run_model_job.apply_async(
            args=[model_job.id, str(data_path), project_description, data_analysis]
        )

    except:
        raise HTTPException(status_code=500, detail="Failed during model training")
    
    return model_job
    


@router.get("/model-job-status/{model_id}", response_model=ModelJobMetadata)
async def get_eda_job_status(
    model_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelJobMetadata:
    if not await user_owns_model_job(user.id, model_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job"
        )
    
    job_meta_data = await get_job_metadata(model_id)
    return job_meta_data


@router.get("/model-job-results/{model_id}", response_model=ModelJobResult)
async def get_eda_job_results(
    model_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelJobResult:

    if not await user_owns_model_job(user.id, model_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(model_id)
    if job_metadata.status == "completed":
        return await get_job_results(model_id)

    else:
        raise HTTPException(
            status_code=500, detail="Integration job is still running")