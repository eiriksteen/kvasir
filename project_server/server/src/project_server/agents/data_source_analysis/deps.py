from dataclasses import dataclass
from pathlib import Path


@dataclass
class DataSourceAnalysisAgentDeps:
    file_path: Path
    # TODO: Add other sources and corresponding deps to interact with them
    # s3_buckets = ...
