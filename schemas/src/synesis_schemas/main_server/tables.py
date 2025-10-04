from pydantic import BaseModel
from typing import List
import uuid


# API Schemas
class TableColumn(BaseModel):
    name: str
    unit: str | None = None
    number_of_significant_digits: int | None = None

class TableConfig(BaseModel):
    title: str
    subtitle: str | None = None
    columns: List[TableColumn]
    showRowNumbers: bool
    maxRows: int | None = None
    sortBy: str | None = None
    sortOrder: str | None = None


class BaseTable(BaseModel):
    id: uuid.UUID
    analysis_result_id: uuid.UUID
    table_config: TableConfig



# CRUD Schemas
class TableCreate(BaseModel):
    analysis_result_id: uuid.UUID
    table_config: TableConfig

class TableUpdate(BaseModel):
    id: uuid.UUID
    table_config: TableConfig