import pandas as pd
from uuid import UUID
from pathlib import Path
from typing import Annotated, Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_table

router = APIRouter()


class ResultTable(BaseModel):
    data: Dict[str, List[Any]]
    index_column: str


@router.post("/get-table/{table_id}")
async def get_table_endpoint(
    table_id: UUID,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> ResultTable:

    client = ProjectClient(bearer_token=token_data.bearer_token)
    table = await get_table(client, table_id)
    table_path = Path(table.table_path)

    if table_path.suffix.lower() != '.parquet':
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table file type. Expected .parquet, got: {table_path.suffix}"
        )
    elif not table_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Table file not found: {table_path}"
        )

    try:
        df = pd.read_parquet(table_path)

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
