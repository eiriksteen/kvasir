from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from synesis_api.modules.orchestrator.agent.prompt import ORCHESTRATOR_SYSTEM_PROMPT
from synesis_api.utils.pydanticai_utils import get_model


model = get_model()


orchestrator_agent = Agent(
    model,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.1)
)
