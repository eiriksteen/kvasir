from pydantic import BaseModel


class TabularFileSavedAPI(BaseModel):
    file_path: str
    file_size_bytes: int
    num_rows: int
    num_columns: int
    content_preview: str


class KeyValueFileSavedAPI(BaseModel):
    file_path: str
    file_size_bytes: int
