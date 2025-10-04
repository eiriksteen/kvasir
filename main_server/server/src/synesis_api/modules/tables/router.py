from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated
import uuid

from synesis_api.modules.tables.service import (
    create_table,
    update_table,
    delete_table,
    get_tables_by_analysis_result_id
)
from synesis_schemas.main_server import BaseTable, TableCreate, TableUpdate
from synesis_schemas.main_server import User
from synesis_api.auth.service import get_current_user

router = APIRouter()


@router.post("/create-table", response_model=BaseTable)
async def create_table_endpoint(
    table_create: TableCreate,
    user: Annotated[User, Depends(get_current_user)] = None
):
    """Create a new table"""
    try:
        return await create_table(table_create)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update-table/{table_id}", response_model=BaseTable)
async def update_table_endpoint(
    table_id: uuid.UUID,
    table_update: TableUpdate, 
    user: Annotated[User, Depends(get_current_user)] = None
):
    """Update an existing table"""
    try:
        # Ensure the table_id in the path matches the one in the request body
        table_update.id = table_id
        return await update_table(table_update)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete-table/{table_id}")
async def delete_table_endpoint(
    table_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
):
    """Delete a table by ID"""
    try:
        await delete_table(table_id)
        return {"message": "Table deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-tables-by-analysis-result-id/{analysis_result_id}", response_model=List[BaseTable])
async def get_tables_by_analysis_result_id_endpoint(
    analysis_result_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)] = None
):
    """Get all tables for a specific analysis result"""
    try:
        return await get_tables_by_analysis_result_id(analysis_result_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))