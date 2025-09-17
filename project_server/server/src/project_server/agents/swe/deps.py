from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    run_on_submit: bool = True
    current_file_name: Optional[str] = None
    run_pylint: bool = False
    history_cutoff_index: int = 1
    current_scripts: Dict[str, str] = field(default_factory=dict)
    history_summary: Optional[str] = None
    test_code_to_append_to_implementation: Optional[str] = None
    structure_ids_to_inject: Optional[List[str]] = None
