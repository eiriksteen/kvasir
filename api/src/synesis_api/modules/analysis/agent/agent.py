from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from synesis_api.utils import run_code_in_container
from synesis_api.modules.analysis.agent.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from dataclasses import dataclass
import pandas as pd


@dataclass
class AnalysisDeps:
    df: pd.DataFrame | None = None



provider = OpenAIProvider(api_key=OPENAI_API_KEY)
model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)
    
analysis_agent = Agent(
    model,
    system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT,
    deps_type=AnalysisDeps,
    name="Analysis Execution Agent",
    model_settings=ModelSettings(temperature=0.1),
    tools=[run_code_in_container],
    retries=3
)