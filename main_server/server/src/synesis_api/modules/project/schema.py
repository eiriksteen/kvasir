import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Project(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    view_port_x: float
    view_port_y: float
    view_port_zoom: float
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str
    mount_group_id: Optional[uuid.UUID] = None
    description: Optional[str] = None


class ProjectViewPortUpdate(BaseModel):
    view_port_x: float
    view_port_y: float
    zoom: float
