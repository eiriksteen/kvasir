import pandas as pd
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.utils.docker_utils import (
    get_host_path_from_container_path,
    create_project_container_if_not_exists
)
from synesis_schemas.project_server import GetTableRequest, ResultTable

router = APIRouter()


@router.post("/get-table")
async def get_table(
    request: GetTableRequest,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> ResultTable:
    client = ProjectClient(bearer_token=token_data.bearer_token)
    # Will raise 403 if user doesn't own it
    project = await get_project(client, request.project_id)
    await create_project_container_if_not_exists(project)

    host_path = get_host_path_from_container_path(
        request.table_path, request.project_id)

    if not host_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Table file not found: {request.table_path}"
        )

    if host_path.suffix.lower() != '.parquet':
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table file type. Expected .parquet, got: {host_path.suffix}"
        )

    try:
        df = pd.read_parquet(host_path)
        data_dict = df.to_dict(orient="list")
        index_column = df.index.name if df.index.name else "index"
        data_dict[index_column] = df.index.tolist()

        return ResultTable(
            data=data_dict,
            index_column=index_column
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read parquet file: {str(e)}"
        )
