from typing import List

from synesis_schemas.main_server import Project
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.messages import ModelMessage
from pydantic_ai.messages import ModelMessagesTypeAdapter

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
from synesis_schemas.main_server import DataSource, Dataset, ModelEntity, Analysis, Pipeline, ProjectGraph


def get_injected_entities_description(
    data_sources: List[DataSource],
    datasets: List[Dataset],
    model_entities: List[ModelEntity],
    analyses: List[Analysis],
    pipelines: List[Pipeline]
) -> str:

    data_sources_description = "\n\n".join(
        [data_source.description_for_agent for data_source in data_sources])
    datasets_description = "\n\n".join(
        [dataset.description_for_agent for dataset in datasets])
    analyses_description = "\n\n".join(
        [analysis.description_for_agent for analysis in analyses])
    model_entities_description = "\n\n".join(
        [model_entity.description_for_agent for model_entity in model_entities])
    pipelines_description = "\n\n".join(
        [pipeline.description_for_agent for pipeline in pipelines])

    data_sources_section = f"<data_sources>\n\n{data_sources_description}\n\n</data_sources>\n\n"
    datasets_section = f"<datasets>\n\n{datasets_description}\n\n</datasets>\n\n"
    analyses_section = f"<analyses>\n\n{analyses_description}\n\n</analyses>\n\n"
    model_entities_section = f"<model_entities>\n\n{model_entities_description}\n\n</model_entities>\n\n"
    pipelines_section = f"<pipelines>\n\n{pipelines_description}\n\n</pipelines>\n\n"

    return f"The injected entities:\n\n{data_sources_section}{datasets_section}{analyses_section}{model_entities_section}{pipelines_section}"


def get_sandbox_environment_description() -> str:
    with open(SANDBOX_PYPROJECT_PATH, "r") as file:
        pyproject_content = file.read()

    env_section = f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" if pyproject_content else ""
    return env_section


def get_project_description(project: Project) -> str:

    desc = (
        "**Project Name:**\n\n" +
        f"{project.name}\n\n" +
        "**Project Description:**\n\n" +
        f"{project.description}\n\n" +
        "**Project Python Package Name:**\n\n" +
        f"{project.python_package_name}\n\n" +
        "**Project Graph:**\n\n" +
        f"{project.graph.model_dump_json(indent=2)}\n\n"
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


def get_model():

    model_id_to_provider_name = {
        "o4-mini": "openai",
        "claude-3-5-sonnet-latest": "anthropic",
        "gemini-2.5-flash": "google",
        "o3": "openai",
        "gemini-2.5-pro": "google",
        "gpt-5": "openai",
        "grok-code-fast-1": "xai"
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
