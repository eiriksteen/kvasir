import uuid
from typing import List, Optional
from pydantic import BaseModel


class FileInRun(BaseModel):
    path: str
    content: str
    old_content: Optional[str] = None
    # For renamed files, stores the original path
    old_name: Optional[str] = None


class RenamedFile(BaseModel):
    old_path: str
    new_path: str
    content: str


class SWEOutput(BaseModel):
    main_script: FileInRun
    changes_made_summary: str
    revert_changes: bool = False


class ImplementationSummary(SWEOutput):
    conversation_id: uuid.UUID
    new_files: List[FileInRun]
    modified_files: List[FileInRun]
    deleted_files: List[FileInRun]
    renamed_files: List[RenamedFile] = []
