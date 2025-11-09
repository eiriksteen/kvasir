import tempfile
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, UploadFile, Form, File, Depends
from uuid import UUID

from project_server.auth import TokenData, decode_token
from project_server.agents.extraction.runner import run_extraction_task
from project_server.client import ProjectClient, get_project
from project_server.app_secrets import SANDBOX_HOST_DIR
from synesis_schemas.project_server import RunExtractionRequest


router = APIRouter()


@router.post("/file")
async def file_data_source(
    files: list[UploadFile] = File(...),
    project_id: UUID = Form(...),
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> RunExtractionRequest:
    """
    Upload one or more files and run extraction jobs on them.
    Copies each file to /app/data/ in the Docker container and triggers extraction.
    """
    project_client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(project_client, project_id)

    paths = []
    for file in files:
        file_content = await file.read()
        target_dir = SANDBOX_HOST_DIR / \
            f"{project_id}" / project.python_package_name / "data" / file.filename
        target_dir.mkdir(parents=True, exist_ok=True)

        with open(target_dir / file.filename, "wb") as f:
            f.write(file_content)

        paths.append((target_dir / file.filename).as_posix())

    extraction_request = RunExtractionRequest(
        project_id=project_id,
        prompt_content=(
            f"The user has added the following files to the project: {', '.join(paths)}. " +
            f"Add the new files as data source entities to the project. " +
            "It is important we do this quickly - Just add the files, do not analyze the rest of the codebase. "
        )
    )

    # Queue the extraction task for this file
    await run_extraction_task.kiq(
        user_id=token_data.user_id,
        extraction_request=extraction_request,
        bearer_token=token_data.bearer_token,
        project=project
    )

    return extraction_request
