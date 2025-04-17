from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from .prompt import CHATBOT_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT
from ..schema import ChatbotOutput
from ....secrets import OPENAI_API_KEY, OPENAI_API_MODEL


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


summary_agent = Agent(
    model,
    system_prompt=SUMMARY_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1),
    result_type=ChatbotOutput,
)


@chatbot_agent.tool_plain
async def get_chatbot_output() -> ChatbotOutput:

    pass

    # output = await summary_agent.run(
    #     f"Here is the conversation: {chatbot_agent.all_messages()}"
    # )

    # return ChatbotOutput(
    #     goal_description=ctx.deps.goal_description,
    #     deliverable_description=ctx.deps.deliverable_description,
    #     task_type=ctx.deps.task_type
    # )
