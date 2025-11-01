import tempfile
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, UploadFile, Form, File, Depends
from uuid import UUID

from project_server.auth import TokenData, decode_token
from project_server.utils.docker_utils import create_project_container_if_not_exists, copy_file_or_directory_to_container
from project_server.agents.extraction.runner import run_extraction_task
from project_server.client import ProjectClient, get_project
from synesis_schemas.project_server import RunExtractionRequest


router = APIRouter()


@router.post("/file")
async def file_data_source(
    file: UploadFile = File(...),
    project_id: UUID = Form(...),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> RunExtractionRequest:
    """
    Upload a file and run extraction job on it.
    Copies the file to /app/data_sources/ in the Docker container and triggers extraction.
    """
    project_client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(project_client, project_id)
    await create_project_container_if_not_exists(project)

    file_content = await file.read()
    container_name = str(project_id)
    project_client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(project_client, project_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        temp_file.write(file_content)
        temp_file_path = Path(temp_file.name)

        try:
            container_file_path = Path(
                f"/app/{project.python_package_name}/data") / file.filename
            await copy_file_or_directory_to_container(
                path=temp_file_path,
                container_save_path=container_file_path,
                container_name=container_name
            )
        finally:
            temp_file_path.unlink()

    extraction_request = RunExtractionRequest(
        project_id=project_id,
        prompt_content=(
            f"The user has placed a new file at {container_file_path.as_posix()} in the container. " +
            f"You should only add a new entity for the file, do not spend time using other tools than getting the right schema and creating the entity. " +
            "It is important we do this quickly. " +
            "If we are dealing with a tabular file such as a CSV, parquet, etc, submit it as a tabular file. "
        )
    )

    # Queue the extraction task
    await run_extraction_task.kiq(
        user_id=token_data.user_id,
        extraction_request=extraction_request,
        bearer_token=token_data.bearer_token
    )

    return extraction_request
