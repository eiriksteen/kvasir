from typing import List
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider


from kvasir_research.utils.code_utils import run_shell_code_in_container
from kvasir_research.utils.docker_utils import get_container_working_directory, list_container_working_directory_contents
from kvasir_research.secrets import ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, XAI_API_KEY, MODEL_TO_USE
from kvasir_research.utils.redis_utils import get_analysis
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


async def get_working_directory_description(container_name: str) -> str:
    pwd, err = await get_container_working_directory(container_name)
    if err:
        raise RuntimeError(f"Failed to get working directory: {err}")

    ls, err = await list_container_working_directory_contents(container_name)
    if err:
        raise RuntimeError(f"Failed to list working directory contents: {err}")

    return f"pwd out: {pwd}\n\nls out:\n{ls}\n\n"


async def get_folder_structure_description(
        container_name: str,
        path: str = "/app",
        n_levels: int = 5,
        max_lines: int = 100) -> str:
    find_cmd = f"find {path} -maxdepth {n_levels} \\( -name '__pycache__' -o -name '*.egg-info' \\) -prune -o -print 2>/dev/null | sort"

    out, err = await run_shell_code_in_container(find_cmd, container_name)

    if err:
        return f"folder structure {n_levels} levels down:\n\nError: {err}"

    if not out.strip():
        return f"folder structure {n_levels} levels down:\n\n(empty or does not exist)"

    all_paths = [line for line in out.split('\n') if line.strip()]

    leaf_paths = []
    for current_path in all_paths:
        is_parent = False
        for other_path in all_paths:
            if other_path != current_path and other_path.startswith(current_path + '/'):
                is_parent = True
                break

        if not is_parent:
            leaf_paths.append(current_path)

    was_truncated = len(leaf_paths) > max_lines

    if was_truncated:
        result_lines = leaf_paths[:max_lines]
        result = '\n'.join(result_lines)
        return f"folder structure {n_levels} levels down:\n\n{result}\n\n[truncated - output exceeded {max_lines} lines]"
    else:
        result = '\n'.join(leaf_paths)
        return f"folder structure {n_levels} levels down:\n\n{result}"


async def get_injected_analyses(analysis_ids: List[str]) -> str:
    analyses_content = []
    for analysis_id in analysis_ids:
        analysis = await get_analysis(analysis_id)
        if analysis:
            analyses_content.append(analysis)
        else:
            logger.warning(f"Analysis {analysis_id} not found in Redis")

    return "\n\n".join(analyses_content) if analyses_content else "(no previous analyses)"
