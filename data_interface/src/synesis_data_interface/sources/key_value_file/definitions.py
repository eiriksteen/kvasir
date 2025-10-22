from typing import List
from dataclasses import dataclass

from synesis_data_interface.sources.base.definitions import DataSourceDefinition


@dataclass
class KeyValueFileDataSourceDefinition(DataSourceDefinition):
    supported_file_types: List[str]


KEY_VALUE_FILE_SOURCE_ID = "key_value_file"
SUPPORTED_KEY_VALUE_FILE_TYPES = [".json", ".jsonl"]
KEY_VALUE_FILE_DATA_SOURCE_DESCRIPTION = f""" 
# Description of the Kvasir data source: {KEY_VALUE_FILE_SOURCE_ID} 
This data source supports key-value file formats.
The current supported file types are: {SUPPORTED_KEY_VALUE_FILE_TYPES}.
The code interface for this data source is:
```python
from typing import Dict, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class KeyValueFileSource:
    file_path: Path
    data: Dict[str, Any]    
```
The module to import from is:

```python
from synesis_data_interface.sources.key_value_file.raw import KeyValueFileSource
```
"""


KEY_VALUE_FILE_DATA_SOURCE_DEFINITION = KeyValueFileDataSourceDefinition(
    name=KEY_VALUE_FILE_SOURCE_ID,
    supported_file_types=SUPPORTED_KEY_VALUE_FILE_TYPES,
    description=KEY_VALUE_FILE_DATA_SOURCE_DESCRIPTION,
    brief_description="File data source for key-value files. "
)
