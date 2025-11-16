import json
from typing import List
from uuid import UUID

from project_server.utils.code_utils import run_shell_code_in_container
from synesis_schemas.main_server import Project, get_entity_graph_description
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from project_server.utils.docker_utils import get_container_working_directory, list_container_working_directory_contents
from project_server.app_secrets import (
    MODEL_TO_USE,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
    SUPPORTED_MODELS,
    XAI_API_KEY,
    SANDBOX_PYPROJECT_PATH
)
from project_server.client import ProjectClient
from project_server.client.requests.entity_graph import get_entity_details


async def get_entities_description(
    client: ProjectClient,
    data_source_ids: List[UUID],
    dataset_ids: List[UUID],
    model_entity_ids: List[UUID],
    analysis_ids: List[UUID],
    pipeline_ids: List[UUID]
) -> str:

    entity_ids: List[UUID] = data_source_ids + dataset_ids + \
        model_entity_ids + analysis_ids + pipeline_ids
    entity_details_response = await get_entity_details(client, entity_ids)

    # Group descriptions by entity type
    data_sources_descriptions = []
    datasets_descriptions = []
    analyses_descriptions = []
    model_entities_descriptions = []
    pipelines_descriptions = []

    for detail in entity_details_response.entity_details:
        if detail.entity_type == "data_source":
            data_sources_descriptions.append(detail.description)
        elif detail.entity_type == "dataset":
            datasets_descriptions.append(detail.description)
        elif detail.entity_type == "analysis":
            analyses_descriptions.append(detail.description)
        elif detail.entity_type == "model_entity":
            model_entities_descriptions.append(detail.description)
        elif detail.entity_type == "pipeline":
            pipelines_descriptions.append(detail.description)

    # Format sections
    data_sources_section = f"<data_sources>\n\n{'\n\n'.join(data_sources_descriptions)}\n\n</data_sources>\n\n" if data_sources_descriptions else ""
    datasets_section = f"<datasets>\n\n{'\n\n'.join(datasets_descriptions)}\n\n</datasets>\n\n" if datasets_descriptions else ""
    analyses_section = f"<analyses>\n\n{'\n\n'.join(analyses_descriptions)}\n\n</analyses>\n\n" if analyses_descriptions else ""
    model_entities_section = f"<model_entities>\n\n{'\n\n'.join(model_entities_descriptions)}\n\n</model_entities>\n\n" if model_entities_descriptions else ""
    pipelines_section = f"<pipelines>\n\n{'\n\n'.join(pipelines_descriptions)}\n\n</pipelines>\n\n" if pipelines_descriptions else ""

    return f"The injected entities:\n\n{data_sources_section}{datasets_section}{analyses_section}{model_entities_section}{pipelines_section}"


def get_sandbox_environment_description() -> str:
    with open(SANDBOX_PYPROJECT_PATH, "r") as file:
        pyproject_content = file.read()

    env_section = f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" if pyproject_content else ""
    return env_section


def get_project_description(project: Project) -> str:
    project_graph_yaml = get_entity_graph_description(project.graph)

    desc = (
        "# PROJECT DESCRIPTION WITH ENTITY GRAPH:\n\n" +
        "**Project Name:**\n\n" +
        f"{project.name}\n\n" +
        "**Project Description:**\n\n" +
        f"{project.description}\n\n" +
        "**Project Python Package Name:**\n\n" +
        f"{project.python_package_name}\n\n" +
        "**Entity Graph:**\n\n" +
        f"{project_graph_yaml}\n\n"
    )

    return desc


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
            f"Unsupported model: {MODEL_TO_USE}, supported models: {SUPPORTED_MODELS}")

    return model


def pydantic_ai_bytes_to_messages(message_list: List[bytes]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for message in message_list:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message))

    return messages
