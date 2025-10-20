import re
import uuid
import pandas as pd
from uuid import UUID
from typing import Union
from pathlib import Path
from pandas.io.json._table_schema import build_table_schema

from project_server.client import ProjectClient, get_data_source
from project_server.app_secrets import RAW_DATA_DIR
from synesis_schemas.main_server import TabularFileDataSourceCreate, KeyValueFileDataSourceCreate, DataSource
from synesis_data_interface.sources.tabular_file.definitions import SUPPORTED_TABULAR_FILE_TYPES, TABULAR_FILE_SOURCE_ID
from synesis_data_interface.sources.tabular_file.raw import TabularFileSource
from synesis_data_interface.sources.key_value_file.definitions import SUPPORTED_KEY_VALUE_FILE_TYPES, KEY_VALUE_FILE_SOURCE_ID
from synesis_data_interface.sources.key_value_file.raw import KeyValueFileSource
from synesis_data_interface.sources.tabular_file.load import load_tabular_file_source
from synesis_data_interface.sources.key_value_file.load import load_key_value_file_source

UUID_FILENAME_SPLITTER = "_fn_"


def _get_valid_python_name_from_path(path: Path) -> str:
    name = path.stem
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    if name and name[0].isdigit():
        name = '_' + name
    if not name:
        name = 'data_source'
    return name


class DataSourceManager:

    def __init__(self, bearer_token: str):
        self.client = ProjectClient(bearer_token)

    async def get_data_source(self, data_source_id: UUID) -> Union[TabularFileSource, KeyValueFileSource]:

        data_source = await get_data_source(self.client, data_source_id)

        if data_source.type == TABULAR_FILE_SOURCE_ID:
            return load_tabular_file_source(data_source.type_fields.file_path)
        elif data_source.type == KEY_VALUE_FILE_SOURCE_ID:
            return load_key_value_file_source(data_source.type_fields.file_path)
        else:
            raise ValueError(
                f"Unsupported data source type: {data_source.type}. Supported types are: tabular_file, key_value_file")

    def save_tabular_file_source(self, file_name: str, file_content: bytes) -> TabularFileDataSourceCreate:

        if Path(file_name).suffix not in SUPPORTED_TABULAR_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {Path(file_name).suffix}. Supported file types are: {SUPPORTED_TABULAR_FILE_TYPES}")

        file_path = RAW_DATA_DIR / \
            f"{uuid.uuid4()}{UUID_FILENAME_SPLITTER}_{file_name}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        df = pd.read_csv(file_path)
        num_rows = len(df)
        num_columns = len(df.columns)
        content_preview = df.head(5).to_string()
        json_schema = build_table_schema(df)

        output = TabularFileDataSourceCreate(
            name=_get_valid_python_name_from_path(Path(file_name)),
            file_name=file_name,
            file_type=Path(file_name).suffix,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
            num_rows=num_rows,
            num_columns=num_columns,
            content_preview=content_preview,
            json_schema=json_schema
        )

        return output

    def save_key_value_file_source(self, file_name: str, file_content: bytes) -> KeyValueFileDataSourceCreate:
        if Path(file_name).suffix not in SUPPORTED_KEY_VALUE_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {Path(file_name).suffix}. Supported file types are: {SUPPORTED_KEY_VALUE_FILE_TYPES}")

        file_path = RAW_DATA_DIR / \
            f"{uuid.uuid4()}{UUID_FILENAME_SPLITTER}_{file_name}"
        with open(file_path, "wb") as f:
            f.write(file_content)

        output = KeyValueFileDataSourceCreate(
            name=_get_valid_python_name_from_path(Path(file_name)),
            file_name=file_name,
            file_type=Path(file_name).suffix,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size
        )

        return output
