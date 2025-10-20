import pandas as pd
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TabularFileSource:
    file_path: Path
    df: pd.DataFrame
