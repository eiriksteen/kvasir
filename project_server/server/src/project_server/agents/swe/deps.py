import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Callable

from project_server.client import ProjectClient
from project_server.agents.runner_base import StreamedCode
from synesis_schemas.main_server import ModelEntity, DataSource, Dataset, Function, Analysis


@dataclass
class SWEAgentDeps:
    cwd: str
    container_name: str
    bearer_token: str
    client: ProjectClient
    conversation_id: uuid.UUID
    functions_injected: List[Function] = field(default_factory=list)
    functions_loaded: List[Function] = field(default_factory=list)
    model_entities_injected: List[ModelEntity] = field(default_factory=list)
    data_sources_injected: List[DataSource] = field(default_factory=list)
    datasets_injected: List[Dataset] = field(default_factory=list)
    analyses_injected: List[Analysis] = field(default_factory=list)
    current_scripts: Dict[str, str] = field(default_factory=dict)
    modified_scripts_old_to_new_name: Dict[str, str] = field(
        default_factory=dict)
    new_scripts: Set[str] = field(default_factory=set)
    log_code: Optional[Callable[StreamedCode, None]] = None
