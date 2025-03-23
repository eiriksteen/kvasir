import uuid
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from .schema import EDAJobMetaData, EDAJobResult
from ..auth.service import (create_api_key,
                            get_current_user,
                            user_owns_eda_job)
from .service import (
    get_job_metadata, 
    get_job_results,
    create_eda_job,
    run_eda_job
)
from ..auth.schema import User
from ..project_spec.schema import DataDescription


router = APIRouter()

@router.post("/call-eda-agent", response_model=EDAJobMetaData)
async def call_eda_agent(
    # problem_id: uuid.UUID,
    # data_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None,

):
    # need a way to load the problem and data description based on a problem_id:
    data_description = DataDescription(
        data_description = "",
        data_type = "",
        data_format = "",
        data_source = "",
        data_size = "",
    )

    try:
        api_key = await create_api_key(user)
        eda_job = await create_eda_job(user.id, api_key.id)
    except:
        raise HTTPException(status_code=500, detail="Failed to create EDA job.")
    
    # data_dir = Path("integrated_data") / f"{user.id}"
    # data_path = data_dir / f"{data_id}.csv" # need a way of getting the data_id
    
    data_dir = Path("files") / "98ca0ae7-5221-4ec0-9bf3-092a0445695a"
    data_path = data_dir / "0b1626e1-d671-47ad-9013-f6ea23b35763.csv"
    project_description = "The goal of this project is to analyze and model the Boston Housing Dataset, with the aim of predicting house prices based on various features. This dataset contains information about different attributes of houses in the Boston area, such as crime rates, average number of rooms, and proximity to employment centers. The project explores the relationship between these attributes and the price of homes, allowing for both descriptive and predictive analytics."
    data_description = """
        The Boston Housing Dataset is a widely used dataset in machine learning and statistics, providing information on various aspects of housing in the Boston area. The dataset contains the following columns:
        CRIM – Crime rate per capita by town.
        ZN – Proportion of residential land zoned for large-scale properties.
        INDUS – Proportion of non-retail business acres per town.
        CHAS – Charles River dummy variable (1 if the property borders the Charles River; 0 otherwise).
        NOX – Nitrogen oxide concentration (parts per 10 million).
        RM – Average number of rooms per dwelling.
        AGE – Proportion of owner-occupied units built before 1940.
        DIS – Weighted distance to employment centers.
        RAD – Index of accessibility to radial highways.
        TAX – Property tax rate per $10,000.
        PTRATIO – Pupil-teacher ratio by town.
        B – Proportion of residents of African American descent by town.
        LSTAT – Percentage of lower status population.
        MEDV – Median value of owner-occupied homes (target variable, in $1,000s).
    """
    
    try:
        summary = run_eda_job.apply_async(
            args=[eda_job.id, user.id, str(data_path), data_description, project_description]
        )
    except:
        raise HTTPException(status_code=500, detail="Failed to run EDA job.")

    return eda_job


@router.get("/eda-job-status/{eda_id}", response_model=EDAJobMetaData)
async def get_eda_job_status(
    eda_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> EDAJobMetaData:
    if not await user_owns_eda_job(user.id, eda_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job"
        )
    
    job_meta_data = await get_job_metadata(eda_id)
    return job_meta_data


@router.get("/eda-job-results/{eda_id}", response_model=EDAJobResult)
async def get_eda_job_results(
    eda_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> EDAJobResult:

    if not await user_owns_eda_job(user.id, eda_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(eda_id)
    if job_metadata.status == "completed":
        return await get_job_results(eda_id)

    else:
        raise HTTPException(
            status_code=500, detail="Integration job is still running")
