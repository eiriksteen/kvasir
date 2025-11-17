from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ImageInDB(BaseModel):
    id: UUID
    image_path: str
    created_at: datetime
    updated_at: datetime


class EchartInDB(BaseModel):
    id: UUID
    chart_script_path: str
    created_at: datetime
    updated_at: datetime


class TableInDB(BaseModel):
    id: UUID
    table_path: str
    created_at: datetime
    updated_at: datetime


class ImageCreate(BaseModel):
    image_path: str


class EchartCreate(BaseModel):
    chart_script_path: str


class TableCreate(BaseModel):
    table_path: str
