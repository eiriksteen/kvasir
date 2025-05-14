from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from synesis_api.modules.chat.agent.prompt import CHATBOT_SYSTEM_PROMPT
from synesis_api.utils import get_model

model = get_model()


chatbot_agent = Agent(
    model,
    system_prompt=CHATBOT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1)
)


# summary_agent = Agent(
#     model,
#     system_prompt=SUMMARY_SYSTEM_PROMPT,
#     model_settings=ModelSettings(temperature=0.1),
#     result_type=ChatbotOutput,
# )
