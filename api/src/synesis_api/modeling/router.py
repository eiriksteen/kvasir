import uuid
import aiofiles
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from .schema import ModelJobResult
from .service import (get_job_metadata,
                      get_job_results,
                      run_model_job)
from ..shared.schema import JobMetadata
from ..shared.service import create_job
from ..auth.schema import User
from ..auth.service import (create_api_key,
                            get_current_user,
                            user_owns_job)


router = APIRouter()


@router.post("/call-model-agent", response_model=JobMetadata)
async def call_model_agent(
    # project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> JobMetadata:
    # project_description = ChatSummary()
    try:
        async with aiofiles.open("files/98ca0ae7-5221-4ec0-9bf3-092a0445695a/c93e686e-f16d-4329-8882-0adce1218126.html", mode='r', encoding='utf-8') as file:
            data_analysis = await file.read()
    except:
        raise HTTPException(
            status_code=404, detail="Could not find data analysis.")

    try:
        api_key = await create_api_key(user)
        model_job = await create_job(user.id, api_key.id, "modeling")
    except:
        raise HTTPException(
            status_code=500, detail="Failed to create model job.")

    data_dir = Path("files") / "98ca0ae7-5221-4ec0-9bf3-092a0445695a"
    data_path = data_dir / "0b1626e1-d671-47ad-9013-f6ea23b35763.csv"
    project_description = "The goal of this project is to analyze and model the Boston Housing Dataset, with the aim of predicting house prices based on various features. This dataset contains information about different attributes of houses in the Boston area, such as crime rates, average number of rooms, and proximity to employment centers. The project explores the relationship between these attributes and the price of homes, allowing for both descriptive and predictive analytics."

    try:
        model = run_model_job.apply_async(
            args=[model_job.id, str(data_path),
                  project_description, data_analysis]
        )

    except:
        raise HTTPException(
            status_code=500, detail="Failed during model training")

    return model_job


@router.get("/model-job-results/{model_id}", response_model=ModelJobResult)
async def get_model_job_results(
    model_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelJobResult:

    if not await user_owns_job(user.id, model_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(model_id)
    if job_metadata.status == "completed":
        return await get_job_results(model_id)

    else:
        raise HTTPException(
            status_code=500, detail="Model job is still running")
