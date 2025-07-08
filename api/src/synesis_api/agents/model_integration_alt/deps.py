import uuid
import httpx
from synesis_api.secrets import GITHUB_TOKEN
from dataclasses import dataclass
from typing import Literal


@dataclass(kw_only=True)
class ModelIntegrationDeps:
    """Dependencies for model integration agents (setup and implementation)"""
    model_id: str
    integration_id: uuid.UUID | None = None
    source: Literal["github", "pip"] | None = None
    container_name: str
    current_script: str | None = None
    client: httpx.AsyncClient = httpx.AsyncClient()
    github_token: str = GITHUB_TOKEN
    cwd: str | None = None
    run_pylint: bool = False
    history_summary: str | None = None
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
