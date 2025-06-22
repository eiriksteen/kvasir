from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from synesis_api.agents.chat.prompt import CHATBOT_SYSTEM_PROMPT
from synesis_api.utils import get_model
from synesis_api.base_schema import BaseSchema
from typing import Literal


class OrchestratorOutput(BaseSchema):
    handoff_agent: Literal["chat", "analysis", "automation"]


model = get_model()


chatbot_agent = Agent(
    model,
    system_prompt=CHATBOT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1)
)
