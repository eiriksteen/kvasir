from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class DataSourceAnalysisAgentDeps:
    file_paths: List[Path]
    # TODO: Add other sources and corresponding deps to interact with them
    # s3_buckets = ...
