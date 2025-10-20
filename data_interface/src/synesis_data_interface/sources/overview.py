from typing import List
from dataclasses import asdict

from synesis_data_interface.sources.base.definitions import DataSourceDefinition
from synesis_data_interface.sources.tabular_file.definitions import TABULAR_FILE_DATA_SOURCE_DEFINITION, TABULAR_FILE_SOURCE_ID
from synesis_data_interface.sources.key_value_file.definitions import KEY_VALUE_FILE_DATA_SOURCE_DEFINITION, KEY_VALUE_FILE_SOURCE_ID

DATA_SOURCES: List[DataSourceDefinition] = [TABULAR_FILE_DATA_SOURCE_DEFINITION,
                                            KEY_VALUE_FILE_DATA_SOURCE_DEFINITION]


def get_data_sources_overview() -> str:
    """Get brief descriptions of all data sources."""
    return "\n".join([f"{source.name}: {source.brief_description}" for source in DATA_SOURCES])


def get_data_source_description(data_source: str) -> str:
    """Get the description of a data source."""
    if data_source == TABULAR_FILE_SOURCE_ID:
        data_dict = asdict(TABULAR_FILE_DATA_SOURCE_DEFINITION)
    elif data_source == KEY_VALUE_FILE_SOURCE_ID:
        data_dict = asdict(KEY_VALUE_FILE_DATA_SOURCE_DEFINITION)
    else:
        raise ValueError(f"Unknown data source: {data_source}")

    return "\n".join([f"{key}: {value}" for key, value in data_dict.items()])
