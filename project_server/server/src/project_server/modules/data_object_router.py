import json
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.client.requests.data_objects import get_data_object, get_object_group
from project_server.utils.docker_utils import read_file_from_container
from project_server.utils.code_utils import run_python_code_in_container
from synesis_schemas.main_server import DataObjectRawData, GetRawDataRequest

router = APIRouter()


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

    script_path = Path(object_group.raw_data_read_script_path)
    try:
        script_content = await read_file_from_container(script_path, container_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read script from container: {str(e)}"
        )

    args_dict = request.args.model_dump()
    execution_code = (
        f"{script_content}\n\n"
        "import json\n"
        f"result = read_raw_data('{data_object.original_id}', **{args_dict})\n"
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

        return DataObjectRawData(
            id=request.object_id,
            modality=object_group.modality,
            data=result_data
        )

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
