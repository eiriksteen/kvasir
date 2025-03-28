from pathlib import Path
from dataclasses import dataclass

@dataclass
class ModelDeps:
    data_path: Path
    data_analysis: str
    problem_description: str