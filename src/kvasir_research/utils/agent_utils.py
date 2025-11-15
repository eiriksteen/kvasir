from typing import List
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider


from kvasir_research.secrets import ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, XAI_API_KEY, MODEL_TO_USE, SANDBOX_PYPROJECT_PATH
from kvasir_research.utils.redis_utils import get_analysis, get_swe_result
from kvasir_research.worker import logger


def get_model():

    model_id_to_provider_name = {
        "o4-mini": "openai",
        "claude-3-5-sonnet-latest": "anthropic",
        "gemini-2.5-flash": "google",
        "o3": "openai",
        "gemini-2.5-pro": "google",
        "gpt-5": "openai",
        "grok-code-fast-1": "xai",
        "grok-4": "xai",
    }

    if model_id_to_provider_name[MODEL_TO_USE] == "anthropic":
        provider = AnthropicProvider(api_key=ANTHROPIC_API_KEY)
        model = AnthropicModel(model_name=MODEL_TO_USE, provider=provider)
    elif model_id_to_provider_name[MODEL_TO_USE] == "google":
        provider = GoogleProvider(api_key=GOOGLE_API_KEY)
        model = GoogleModel(model_name=MODEL_TO_USE, provider=provider)
    elif model_id_to_provider_name[MODEL_TO_USE] == "openai":
        provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        model = OpenAIChatModel(model_name=MODEL_TO_USE, provider=provider)
    elif model_id_to_provider_name[MODEL_TO_USE] == "xai":
        provider = GrokProvider(api_key=XAI_API_KEY)
        model = OpenAIChatModel(model_name=MODEL_TO_USE, provider=provider)
    else:
        raise ValueError(
            f"Unsupported model: {MODEL_TO_USE}, supported models: {model_id_to_provider_name.keys()}")

    return model


async def get_injected_analyses(analysis_ids: List[str]) -> str:
    analyses_content = []
    for analysis_id in analysis_ids:
        analysis = await get_analysis(analysis_id)
        if analysis:
            analyses_content.append(analysis)
        else:
            logger.warning(f"Analysis {analysis_id} not found in Redis")

    return "\n\n".join(analyses_content) if analyses_content else "(no previous analyses)"


async def get_injected_swe_runs(swe_run_ids: List[str]) -> str:
    swe_runs_content = []
    for swe_run_id in swe_run_ids:
        swe_result = await get_swe_result(swe_run_id)
        if swe_result:
            swe_runs_content.append(swe_result)
        else:
            logger.warning(f"SWE run {swe_run_id} not found in Redis")

    return "\n\n".join(swe_runs_content) if swe_runs_content else "(no previous SWE runs)"


def get_pyproject_for_env_description() -> str:
    with open(SANDBOX_PYPROJECT_PATH, "r") as f:
        dockerfile_content = f.read()

    return dockerfile_content
