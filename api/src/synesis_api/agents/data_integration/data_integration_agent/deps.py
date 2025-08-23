from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class DataIntegrationAgentDeps:
    data_source_descriptions: List[str]
    file_paths: List[Path]
    api_key: str
    # No target data description as this will be provided in the user prompt
