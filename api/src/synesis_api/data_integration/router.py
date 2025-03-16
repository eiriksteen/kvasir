import uuid
import aiofiles
import pandas as pd
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from io import StringIO
from pathlib import Path
from .service import (
    run_integration_job,
    create_integration_job,
    get_job_metadata,
    validate_restructured_data,
    insert_restructured_time_series_data_to_db,
    get_job_results
)
from .schema import IntegrationJobMetadata, DataSubmissionResponse, IntegrationJobResult
from ..auth.schema import User
from ..auth.service import (create_api_key,
                            get_current_user,
                            get_user_from_api_key,
                            delete_api_key,
                            user_owns_integration_job)


router = APIRouter()


@router.post("/call_integration_agent", response_model=IntegrationJobMetadata)
async def call_integration_agent(
    file: UploadFile,
    data_description: str = Form(...),
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobMetadata:
    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=400, detail="The file must be a CSV file")

    data_path, api_key = None, None
    try:
        user_dir = Path("files") / f"{user.id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        data_path = user_dir / f"{uuid.uuid4()}.csv"

        contents = await file.read()
        async with aiofiles.open(data_path, mode="wb") as f:
            await f.write(contents)

        api_key = await create_api_key(user)
        integration_job = await create_integration_job(user.id, api_key.id)

        task = run_integration_job.apply_async(
            args=[integration_job.id,
                  api_key.key,
                  str(data_path),
                  data_description]
        )

        if task.status == "FAILURE":
            raise HTTPException(
                status_code=500, detail="Failed to process the integration request")

        return integration_job # should you not reload the integration job so the completed_at will be filled

    except Exception as e:
        if data_path and data_path.exists():
            data_path.unlink()
        if api_key:
            await delete_api_key(user)
        raise HTTPException(
            status_code=500, detail=f"Failed to process the integration request: {str(e)}")


@router.get("/integration_job_status/{job_id}", response_model=IntegrationJobMetadata)
async def get_integration_job_status(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobMetadata:

    if not await user_owns_integration_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)
    return job_metadata


@router.get("/integration_job_results/{job_id}", response_model=IntegrationJobResult)
async def get_integration_job_results(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> IntegrationJobResult:

    if not await user_owns_integration_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    job_metadata = await get_job_metadata(job_id)
    if job_metadata.status == "completed":
        return await get_job_results(job_id)

    else:
        raise HTTPException(
            status_code=500, detail="Integration job is still running")


# TODO: Make efficient
@router.post("/restructured_data", response_model=DataSubmissionResponse)
async def post_restructured_data(
    file: UploadFile,
    data_description: str = Form(...),
    dataset_name: str = Form(...),
    data_modality: str = Form(...),
    index_first_level: str = Form(...),
    index_second_level: str | None = Form(None),
    user: str = Depends(get_user_from_api_key)
) -> DataSubmissionResponse:

    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=400, detail="The file must be a CSV file")

    content = await file.read()
    df = pd.read_csv(StringIO(content.decode("utf-8")))
    df = validate_restructured_data(
        df,
        index_first_level,
        index_second_level
    )

    if data_modality == "time_series":
        dataset_id = await insert_restructured_time_series_data_to_db(
            df,
            data_description,
            dataset_name,
            data_modality,
            user.id
        )
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported data modality")

    user_dir = Path("integrated_data") / f"{user.id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    out_file_path = user_dir / f"{dataset_id}.csv"

    try:
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            await out_file.write(df.reset_index().to_csv(index=False).encode("utf-8"))
    except OSError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write output file: {str(e)}")

    return DataSubmissionResponse(dataset_id=dataset_id)
