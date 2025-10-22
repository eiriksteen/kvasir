from typing import List

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.messages import ModelMessage
from pydantic_ai.messages import ModelMessagesTypeAdapter

from project_server.app_secrets import MODEL_TO_USE, ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, SUPPORTED_MODELS, XAI_API_KEY,  MODELS_MODULE, MODELS_MODULE_TMP, SANDBOX_PYPROJECT_PATH
from synesis_schemas.main_server import DataSource, Dataset, ModelEntity, Analysis
from synesis_data_interface.structures.overview import get_data_structure_description
from synesis_data_interface.sources.overview import get_data_source_description


def get_injected_entities_description(
    data_sources: List[DataSource],
    datasets: List[Dataset],
    model_entities: List[ModelEntity],
    analyses: List[Analysis],
    tmp: bool = True
) -> str:

    data_sources_description = "\n\n".join(
        [data_source.description_for_agent for data_source in data_sources])
    datasets_description = "\n\n".join(
        [dataset.description_for_agent for dataset in datasets])
    analyses_description = "\n\n".join(
        [analysis.description_for_agent for analysis in analyses])
    model_entities_description = "\n\n".join(
        [model_entity.description_for_agent for model_entity in model_entities])

    data_sources_section = f"<data_sources>\n\n{data_sources_description}\n\n</data_sources>\n\n"
    datasets_section = f"<datasets>\n\n{datasets_description}\n\n</datasets>\n\n"
    analyses_section = f"<analyses>\n\n{analyses_description}\n\n</analyses>\n\n"
    model_entities_section = f"<model_entities>\n\n{model_entities_description}\n\n</model_entities>\n\n"

    if tmp:
        model_entities_section = model_entities_section.replace(
            MODELS_MODULE, MODELS_MODULE_TMP)

    return f"The injected entities:\n\n{data_sources_section}{datasets_section}{analyses_section}{model_entities_section}"


def get_sandbox_environment_description() -> str:
    with open(SANDBOX_PYPROJECT_PATH, "r") as file:
        pyproject_content = file.read()

    env_section = f"\n\nThe pyproject.toml defining your environment is:\n\n[START_OF_PYPROJECT_TOML]{pyproject_content}[END_OF_PYPROJECT_TOML]\n\n" if pyproject_content else ""
    return env_section


def get_structure_descriptions_from_datasets(datasets: List[Dataset]) -> str:
    structure_descriptions = {}
    for dataset in datasets:
        for structure in dataset.object_groups:
            structure_type = structure.structure_type
            structure_descriptions[structure_type] = get_data_structure_description(
                structure_type)

    descriptions_joined = "\n\n".join(structure_descriptions.values())
    return f"The definitions of the structures found in the injected datasets are:\n\n<data_structures>\n\n{descriptions_joined}\n\n</data_structures>\n\n"


def get_data_source_type_descriptions_from_data_sources(data_sources: List[DataSource]) -> str:
    data_source_descriptions = {}
    for data_source in data_sources:
        data_source_descriptions[data_source.type] = get_data_source_description(
            data_source.type)

    descriptions_joined = "\n\n".join(data_source_descriptions.values())
    return f"The definitions of the data source types found in the injected data sources are:\n\n<data_sources>\n\n{descriptions_joined}\n\n</data_sources>\n\n"


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
