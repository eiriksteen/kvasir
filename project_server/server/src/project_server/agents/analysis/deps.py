import uuid
from dataclasses import dataclass

from project_server.client import ProjectClient
from synesis_schemas.project_server import RunAnalysisRequest


@dataclass
class AnalysisDeps:
    analysis_request: RunAnalysisRequest
    client: ProjectClient
    run_id: uuid.UUID
