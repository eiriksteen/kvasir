import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from project_server.client import ProjectClient
from synesis_schemas.main_server import ObjectGroup


@dataclass
class ChartDeps:
    container_name: str
    client: ProjectClient
    project_id: uuid.UUID
    datasets_injected: List[uuid.UUID] = field(default_factory=list)
    data_sources_injected: List[uuid.UUID] = field(default_factory=list)
    # Pre-executed code with computed variables
    base_code: Optional[str] = None
    # If set, chart is for object group (takes object_id param)
    object_group: Optional[ObjectGroup] = None
