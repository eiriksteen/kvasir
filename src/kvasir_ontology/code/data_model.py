from typing import List, Optional
from pydantic import BaseModel


class CodebaseFile(BaseModel):
    path: str
    content: str


class CodebaseFilePaginated(BaseModel):
    path: str
    content: str
    offset: int
    limit: int
    total_lines: int
    has_more: bool


class CodebasePath(BaseModel):
    path: str
    is_file: bool
    sub_paths: List['CodebasePath'] = []


# Resolve forward reference for recursive type
CodebasePath.model_rebuild()
