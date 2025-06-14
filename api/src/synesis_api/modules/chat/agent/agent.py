from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from synesis_api.modules.chat.agent.prompt import CHATBOT_SYSTEM_PROMPT
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from synesis_api.base_schema import BaseSchema
from typing import Literal

class OrchestratorOutput(BaseSchema):
    handoff_agent: Literal["chat", "analysis", "automation"]


provider = OpenAIProvider(api_key=OPENAI_API_KEY)

model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)


chatbot_agent = Agent(
    model,
    system_prompt=CHATBOT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1)
)