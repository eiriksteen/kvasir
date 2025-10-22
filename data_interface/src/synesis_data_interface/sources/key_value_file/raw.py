from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class KeyValueFileSource:
    file_path: Path
    data: Dict[str, Any]
