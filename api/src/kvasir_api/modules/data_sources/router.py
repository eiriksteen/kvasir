import io
from typing import Annotated, List
from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from uuid import UUID

from kvasir_api.modules.data_sources.service import get_data_sources_service
from kvasir_ontology.entities.data_source.interface import DataSourceInterface
from kvasir_ontology.entities.data_source.data_model import (
    DataSource,
    DataSourceCreate,
    DataSourceDetailsCreate,
)


router = APIRouter()


# TODO:
# - DB should only commit on end to avoid partial updates
# - Figure out whether to raise http exception in service or just router
# - Possibly simplify structure of router / service / agent


@router.get("/data-sources", response_model=List[DataSource])
async def fetch_data_sources(
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> List[DataSource]:
    return await data_source_service.get_data_sources()


@router.get("/data-source/{data_source_id}", response_model=DataSource)
async def fetch_data_source(
    data_source_id: UUID,
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> DataSource:
    return await data_source_service.get_data_source(data_source_id)


@router.get("/data-sources-by-ids", response_model=List[DataSource])
async def fetch_data_sources_by_ids(
    data_source_ids: List[UUID],
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> List[DataSource]:
    """Get data sources by IDs"""
    return await data_source_service.get_data_sources(data_source_ids)


@router.post("/data-source", response_model=DataSource)
async def create_data_source_endpoint(
    data_source_create: DataSourceCreate,
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> DataSource:
    """Create a data source with conditional type-specific fields"""
    try:
        return await data_source_service.create_data_source(data_source_create)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400, detail=f"Invalid data source: {e}")


@router.post("/data-source-details", response_model=DataSource)
async def add_data_source_details_endpoint(
    details_create: DataSourceDetailsCreate,
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> DataSource:
    """Add details to an existing data source"""
    try:
        return await data_source_service.add_data_source_details(
            details_create.data_source_id, details_create)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400, detail=f"Invalid data source details: {e}")


@router.post("/files-data-sources", response_model=List[DataSource])
async def create_files_data_sources_endpoint(
    files: List[UploadFile],
    mount_node_id: Annotated[UUID, Form()],
    data_source_service: Annotated[DataSourceInterface,
                                   Depends(get_data_sources_service)]
) -> List[DataSource]:
    """Create files data sources"""
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400, detail="No files provided")

    try:
        file_bytes = [io.BytesIO(await file.read()) for file in files]
        file_names = [file.filename for file in files]
        return await data_source_service.create_files_data_sources(file_bytes, file_names, mount_node_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400, detail=f"Invalid files or data: {e}")
