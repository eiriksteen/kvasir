import uuid
import httpx
from synesis_api.app_secrets import GITHUB_TOKEN
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(kw_only=True)
class ModelIntegrationDeps:
    """Dependencies for model integration agents (setup and implementation)"""
    model_id: str
    source: Literal["github", "pip", "source_code"]
    container_name: str
    integration_id: Optional[uuid.UUID] = None
    current_script: Optional[str] = None
    client: httpx.AsyncClient = httpx.AsyncClient()
    github_token: str = GITHUB_TOKEN
    cwd: Optional[str] = None
    run_pylint: bool = False
    history_summary: Optional[str] = None
    history_cutoff_index: int = 1
    stage: Literal["model_analysis",
                   "implementation_planning",
                   "training",
                   "inference"] | None = None
    # Implementation-specific fields
    current_task: Literal["classification",
                          "regression",
                          "segmentation",
                          "forecasting"] | None = None
    modality: Literal["time_series", "image", "text"] | None = None
