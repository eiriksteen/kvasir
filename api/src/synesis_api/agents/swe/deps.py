from dataclasses import dataclass, field
from typing import Optional, List, Callable


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    run_pylint: bool = False
    history_cutoff_index: int = 1
    current_script: Optional[str] = None
    history_summary: Optional[str] = None
    implementation_validation_fns: List[Callable] = field(default_factory=[])
