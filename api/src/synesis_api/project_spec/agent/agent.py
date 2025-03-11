from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from .prompt import CHATBOT_SYSTEM_PROMPT
from ..schema import ChatbotOutput
from ...secrets import OPENAI_API_KEY

model = OpenAIModel(
    "gpt-4o",
    api_key=OPENAI_API_KEY
)


chatbot_agent = Agent(
    model,
    system_prompt=CHATBOT_SYSTEM_PROMPT,
    result_type=ChatbotOutput,
    model_settings=ModelSettings(
        temperature=0.1
    )
)
