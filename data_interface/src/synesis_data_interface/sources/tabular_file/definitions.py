from dataclasses import dataclass
from typing import List

from synesis_data_interface.sources.base.definitions import DataSourceDefinition


@dataclass
class TabularFileDataSourceDefinition(DataSourceDefinition):
    supported_file_types: List[str]


TABULAR_FILE_SOURCE_ID = "tabular_file"
SUPPORTED_TABULAR_FILE_TYPES = [".csv", ".parquet", ".json", ".jsonl", ".xlsx"]
TABULAR_FILE_DATA_SOURCE_DESCRIPTION = f"""
# Description of the Kvasir data source: {TABULAR_FILE_SOURCE_ID}
This data source supports tabular file formats. 
The current supported file types are: {SUPPORTED_TABULAR_FILE_TYPES}. 
The code interface for this data source is:
```python
import pandas as pd
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TabularFileSource:
    file_path: Path
    df: pd.DataFrame
```
The module to import from is: 

```python
from synesis_data_interface.sources.tabular_file.raw import TabularFileSource
```
"""


TABULAR_FILE_DATA_SOURCE_DEFINITION = TabularFileDataSourceDefinition(
    name=TABULAR_FILE_SOURCE_ID,
    supported_file_types=SUPPORTED_TABULAR_FILE_TYPES,
    description=TABULAR_FILE_DATA_SOURCE_DESCRIPTION,
    brief_description="File data source for tabular files. "
)
