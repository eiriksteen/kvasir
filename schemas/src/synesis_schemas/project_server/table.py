from uuid import UUID
from typing import Dict, Any, List
from pydantic import BaseModel


class GetTableRequest(BaseModel):
    """Request to get table data from a parquet file"""
    project_id: UUID
    table_path: str


class ResultTable(BaseModel):
    """Response containing table data from a parquet file"""
    data: Dict[str, List[Any]]
    index_column: str

