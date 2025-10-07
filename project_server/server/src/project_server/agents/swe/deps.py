from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set


@dataclass
class FunctionToInject:
    filename: str
    script_path: str
    docstring: str
    module: str


@dataclass
class ModelToInject:
    filename: str
    script_path: str
    module: str
    model_class_docstring: str
    training_function_docstring: str
    inference_function_docstring: str


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    run_on_submit: bool = True
    run_pylint: bool = False
    history_cutoff_index: int = 1
    functions_injected: List[FunctionToInject] = field(default_factory=list)
    models_injected: List[ModelToInject] = field(default_factory=list)
    current_scripts: Dict[str, str] = field(default_factory=dict)
    modified_scripts: Set[str] = field(default_factory=set)
    new_scripts: Set[str] = field(default_factory=set)
    input_scripts: Optional[Dict[str, str]] = None
    history_summary: Optional[str] = None
    test_code_to_append_to_implementation: Optional[str] = None
    structure_ids_to_inject: Optional[List[str]] = None
    inject_synthetic_data_descriptions: bool = False
    log: bool = False
