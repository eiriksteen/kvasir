from dataclasses import dataclass
from typing import List

from synesis_schemas.main_server import DataSource


@dataclass
class DataIntegrationAgentDeps:
    data_sources: List[DataSource]
    # No target data description as this will be provided in the user prompt
