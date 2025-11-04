import json
from typing import Annotated, Union
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.client.requests.data_objects import get_data_object, get_object_group
from project_server.utils.docker_utils import read_file_from_container
from project_server.utils.code_utils import run_python_code_in_container
from synesis_schemas.main_server import DataObjectRawData, GetRawDataRequest, TimeSeriesRawDataParams

router = APIRouter()


MAX_READ_TIME_SERIES_LENGTH = 512


# def _validate_read_args(args:  Union[TimeSeriesRawDataParams]) -> None:
#     #


@router.post("/read-raw-data")
async def read_raw_data(
    request: GetRawDataRequest,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> DataObjectRawData:

    client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(client, request.project_id)
    container_name = str(project.id)

    data_object = await get_data_object(client, request.object_id)
    object_group = await get_object_group(client, data_object.group_id, include_objects=False)

    if not object_group.raw_data_read_script_path:
        raise HTTPException(
            status_code=404,
            detail=f"No raw data read script found for object group {object_group.id}"
        )

    if not object_group.raw_data_read_function_name:
        raise HTTPException(
            status_code=404,
            detail=f"Found script, but no raw data read function name found for object group {object_group.id}. This should not happen."
        )

    script_path = Path(object_group.raw_data_read_script_path)
    try:
        script_content = await read_file_from_container(script_path, container_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read script from container: {str(e)}"
        )

    args_parts = []
    for key, value in request.args.model_dump().items():
        if isinstance(value, datetime):
            iso_str = value.replace(tzinfo=None).isoformat()
            args_parts.append(f"{key}='{iso_str}'")
        else:
            args_parts.append(f"{key}={repr(value)}")

    args_str = ", ".join(args_parts)
    execution_code = (
        "import json\n"
        f"{script_content}\n\n"
        f"result = {object_group.raw_data_read_function_name}('{data_object.original_id}', {args_str})\n"
        "print(json.dumps(result, default=str))"
    )

    try:
        out, err = await run_python_code_in_container(execution_code, container_name)

        if err:
            raise HTTPException(
                status_code=500,
                detail=f"Script execution error: {err}"
            )

        result_data = json.loads(out.strip())
        return DataObjectRawData(**result_data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse script output: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute script: {str(e)}"
        )
