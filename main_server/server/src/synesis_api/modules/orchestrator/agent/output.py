from typing import Literal, Optional
from pydantic import model_validator, BaseModel


class OrchestratorOutput(BaseModel):
    handoff_agent: Literal["chat",
                           "analysis",
                           "pipeline",
                           "data_integration"]
    run_name: Optional[str] = None

    @model_validator(mode='after')
    def validate_run_name(self) -> 'OrchestratorOutput':
        if self.handoff_agent != "chat" and self.run_name is None:
            raise ValueError(
                "run_name is required when handoff_agent is not 'chat'")
        return self
