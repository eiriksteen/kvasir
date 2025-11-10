from typing import List
from pydantic import BaseModel


class ProjectFile(BaseModel):
    path: str
    content: str


class ProjectPath(BaseModel):
    path: str
    is_file: bool
    sub_paths: List['ProjectPath'] = []


# Resolve forward reference for recursive type
ProjectPath.model_rebuild()
