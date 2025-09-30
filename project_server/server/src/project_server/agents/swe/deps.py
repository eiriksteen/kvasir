from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set


@dataclass
class ScriptToInject:
    script_name: str
    script_path: str


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    run_on_submit: bool = True
    run_pylint: bool = False
    history_cutoff_index: int = 1
    current_scripts: Dict[str, str] = field(default_factory=dict)
    modified_scripts: Set[str] = field(default_factory=set)
    input_scripts: Optional[Dict[str, str]] = None
    history_summary: Optional[str] = None
    test_code_to_append_to_implementation: Optional[str] = None
    structure_ids_to_inject: Optional[List[str]] = None
    inject_synthetic_data_descriptions: bool = False
    log: bool = False
