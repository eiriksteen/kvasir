from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    current_file_name: Optional[str] = None
    run_pylint: bool = False
    history_cutoff_index: int = 1
    current_scripts: Dict[str, str] = field(default_factory=dict)
    history_summary: Optional[str] = None
    implementation_validation_fns: List[Callable] = field(default_factory=[])
