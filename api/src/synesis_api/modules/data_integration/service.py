import uuid
import aiofiles
from typing import List
from fastapi import HTTPException, UploadFile
from sqlalchemy import insert, select, delete
from synesis_api.modules.data_integration.schema import (
    IntegrationJobResultInDB,
    IntegrationJobLocalInput,
    LocalDirectoryDataSource,
    LocalDirectoryFile
)
from synesis_api.modules.data_integration.models import (
    data_integration_job_result,
    data_integration_job_local_input,
    local_directory_data_source,
    local_directory_file,
)
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.secrets import DATA_INTEGRATION_LOCAL_DIRECTORY_PATH


async def create_local_directory_data_source(
    directory_name: str,
    description: str,
    user_id: uuid.UUID,
    files: list[UploadFile]
) -> LocalDirectoryDataSource:

    # Iterate over files and save local_directory_file models for all, then save local_directory_data_source model
    # Return the local_directory_data_source model

    local_directory_data_source_model = LocalDirectoryDataSource(
        id=uuid.uuid4(),
        directory_name=directory_name,
        description=description,
        user_id=user_id
    )

    await execute(
        insert(local_directory_data_source).values(
            local_directory_data_source_model.model_dump()),
        commit_after=True
    )

    file_records: list[LocalDirectoryFile] = []

    output_dir = DATA_INTEGRATION_LOCAL_DIRECTORY_PATH / \
        str(local_directory_data_source_model.id) / directory_name
    output_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_record = LocalDirectoryFile(
            file_name=file.filename,
            file_path=output_dir / file.filename,
            file_type=file.content_type
        )
        file_records.append(file_record)

        async with aiofiles.open(file_record.file_path, mode="wb") as f:
            await f.write(await file.read())

    await execute(
        insert(local_directory_file).values(
            [file_record.model_dump() for file_record in file_records]),
        commit_after=True
    )

    return local_directory_data_source_model


async def get_local_directory_data_source_from_ids(data_directory_ids: List[uuid.UUID]) -> List[LocalDirectoryDataSource]:

    data_directory = await fetch_all(
        select(local_directory_data_source).where(
            local_directory_data_source.c.id.in_(data_directory_ids)),
        commit_after=True
    )

    return [LocalDirectoryDataSource(**data_directory) for data_directory in data_directory]


async def create_integration_result(result: IntegrationJobResultInDB):
    await execute(
        insert(data_integration_job_result).values(
            result.model_dump()),
        commit_after=True
    )


async def delete_integration_result(job_id: uuid.UUID):
    await execute(
        delete(data_integration_job_result).where(
            data_integration_job_result.c.job_id == job_id),
        commit_after=True
    )


async def get_job_results_from_job_id(job_id: uuid.UUID) -> IntegrationJobResultInDB:
    # get results from integration_jobs_results
    results = await fetch_one(
        select(data_integration_job_result).where(
            data_integration_job_result.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobResultInDB(**results)


async def get_job_results_from_dataset_id(dataset_id: uuid.UUID) -> List[IntegrationJobResultInDB]:
    # get results from integration_jobs_results
    results = await fetch_all(
        select(data_integration_job_result).where(
            data_integration_job_result.c.dataset_id == dataset_id),
        commit_after=True
    )

    return [IntegrationJobResultInDB(**result) for result in results]


async def create_integration_input(input: IntegrationJobLocalInput, data_source: str):

    if data_source == "local":
        await execute(
            insert(data_integration_job_local_input).values(
                input.model_dump()),
            commit_after=True
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid data source, currently only local is supported"
        )


async def get_integration_input(job_id: uuid.UUID) -> IntegrationJobLocalInput:

    # Currently only local source is supported

    input = await fetch_one(
        select(data_integration_job_local_input).where(
            data_integration_job_local_input.c.job_id == job_id),
        commit_after=True
    )

    return IntegrationJobLocalInput(**input)


async def get_dataset_id_from_job_id(job_id: uuid.UUID) -> uuid.UUID:
    dataset_id = await fetch_one(
        select(data_integration_job_result).where(
            data_integration_job_result.c.job_id == job_id),
        commit_after=True
    )

    return dataset_id["dataset_id"]
