import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Callable

from project_server.client import ProjectClient
from project_server.agents.runner_base import CodeForLog


@dataclass
class FunctionInjected:
    filename: str
    script_path: str
    docstring: str
    module_path: str


@dataclass
class ModelInjected:
    filename: str
    script_path: str
    module_path: str
    model_class_docstring: str
    training_function_docstring: str
    inference_function_docstring: str


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    client: ProjectClient
    history_cutoff_index: int = 1
    functions_injected: List[FunctionInjected] = field(default_factory=list)
    models_injected: List[ModelInjected] = field(default_factory=list)
    current_scripts: Dict[str, str] = field(default_factory=dict)
    modified_scripts_old_to_new_name: Dict[str, str] = field(
        default_factory=dict)
    new_scripts: Set[str] = field(default_factory=set)
    history_summary: Optional[str] = None
    test_code_to_append_to_implementation: Optional[str] = None
    structure_ids_to_inject: Optional[List[str]] = None
    inject_synthetic_data_descriptions: bool = False
    log_code: Optional[Callable[CodeForLog, None]] = None
