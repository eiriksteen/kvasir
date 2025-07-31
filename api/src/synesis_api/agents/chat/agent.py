from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from synesis_api.agents.chat.prompt import CHATBOT_SYSTEM_PROMPT
from synesis_api.utils import get_model
from synesis_api.base_schema import BaseSchema
from typing import Literal, Optional
from pydantic import model_validator


class OrchestratorOutput(BaseSchema):
    handoff_agent: Literal["chat",
                           "analysis",
                           "automation",
                           "data_integration"]
    run_name: Optional[str] = None

    @model_validator(mode='after')
    def validate_run_name(self) -> 'OrchestratorOutput':
        if self.handoff_agent != "chat" and self.run_name is None:
            raise ValueError(
                "run_name is required when handoff_agent is not 'chat'")
        return self


model = get_model()


chatbot_agent = Agent(
    model,
    system_prompt=CHATBOT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1)
)
