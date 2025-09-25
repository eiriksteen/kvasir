from dataclasses import dataclass
from typing import List
from logging import Logger

from synesis_schemas.main_server import DataSourceFull


@dataclass
class DataIntegrationAgentDeps:
    bearer_token: str
    data_sources: List[DataSourceFull]
    # No target data description as this will be provided in the user prompt
