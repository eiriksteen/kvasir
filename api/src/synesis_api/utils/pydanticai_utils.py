from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from synesis_api.secrets import MODEL_TO_USE, ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, SUPPORTED_MODELS


def get_model():

    model_id_to_provider_name = {
        "o4-mini": "openai",
        "claude-3-5-sonnet-latest": "anthropic",
        "gemini-2.5-flash": "google",
        "o3": "openai",
        "gemini-2.5-pro": "google"
    }

    if model_id_to_provider_name[MODEL_TO_USE] == "anthropic":
        provider = AnthropicProvider(api_key=ANTHROPIC_API_KEY)
        model = AnthropicModel(model_name=MODEL_TO_USE, provider=provider)
    elif model_id_to_provider_name[MODEL_TO_USE] == "google":
        provider = GoogleProvider(api_key=GOOGLE_API_KEY)
        model = GoogleModel(model_name=MODEL_TO_USE, provider=provider)
    elif model_id_to_provider_name[MODEL_TO_USE] == "openai":
        provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        model = OpenAIModel(model_name=MODEL_TO_USE, provider=provider)
    else:
        raise ValueError(
            f"Unsupported model: {MODEL_TO_USE}, supported models: {SUPPORTED_MODELS}")

    return model
