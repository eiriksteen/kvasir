import json
from typing import Annotated
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.utils.docker_utils import read_file_from_container
from project_server.utils.code_utils import run_python_code_in_container
from synesis_schemas.project_server import EChartsOption

router = APIRouter()


class GetChartRequest(BaseModel):
    """Request to get chart configuration"""
    project_id: UUID
    script_path: str
    original_object_id: str | None = None  # Optional - only for per-object charts
    add_legend: bool = True


@router.post("/get-chart")
async def get_chart(
    request: GetChartRequest,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> EChartsOption:
    """
    Execute a chart generation script and return the ECharts configuration.

    This endpoint:
    1. Verifies the user owns the project
    2. Reads the chart script from the container
    3. Executes the script with the given original_object_id
    4. Returns the validated EChartsConfig
    """

    print("get_chart", request)

    client = ProjectClient(bearer_token=token_data.bearer_token)
    # Will raise 403 if user doesn't own it
    await get_project(client, request.project_id)
    container_name = str(request.project_id)

    # Read the chart script from the container
    script_path = Path(request.script_path)
    try:
        script_content = await read_file_from_container(script_path, container_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read chart script from container: {str(e)}"
        )

    try:
        out, err = await run_python_code_in_container(script_content, container_name)

        if err:
            raise HTTPException(
                status_code=500,
                detail=f"Chart script execution error: {err}"
            )

        result_data = json.loads(out.strip())

        # Validate with full schema - allows any valid ECharts config
        chart_config = EChartsOption(**result_data)
        return chart_config

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse chart script output: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute chart script: {str(e)}"
        )
