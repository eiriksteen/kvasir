from uuid import UUID
from pydantic import BaseModel


class FileSavedAPI(BaseModel):
    file_id: UUID
    file_path: str
