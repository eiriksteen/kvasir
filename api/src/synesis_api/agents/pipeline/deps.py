from dataclasses import dataclass
from pydantic_ai import Agent


@dataclass
class PipelineAgentDeps:
    container_name: str
