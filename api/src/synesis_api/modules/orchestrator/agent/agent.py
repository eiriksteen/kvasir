from dataclasses import dataclass
from typing import Literal
from pydantic_ai.models.openai import OpenAIModel
from ....secrets import OPENAI_API_MODEL, OPENAI_API_KEY
from pydantic_ai.providers.openai import OpenAIProvider
from .prompt import SYSTEM_PROMPT
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
provider = OpenAIProvider(api_key=OPENAI_API_KEY)
from ....base_schema import BaseSchema

class OrchestratorOutput(BaseSchema):
    handoff_agent: Literal["chat", "analysis", "automation"]


model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)

orchestrator_agent = Agent(
    model,
    system_prompt=SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1),
    result_type=OrchestratorOutput,
)

