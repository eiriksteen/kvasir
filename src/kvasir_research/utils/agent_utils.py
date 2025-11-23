from typing import List, Sequence
from uuid import UUID
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse

from kvasir_research.secrets import ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, XAI_API_KEY, MODEL_TO_USE, SANDBOX_PYPROJECT_PATH
from kvasir_research.utils.redis_utils import get_analysis, get_swe_result
# from kvasir_research.worker import logger


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


async def get_injected_analyses(analysis_ids: List[UUID]) -> str:
    analyses_content = []
    for analysis_id in analysis_ids:
        analysis = await get_analysis(analysis_id)
        if analysis:
            analyses_content.append(analysis)

    return "\n\n".join(analyses_content) if analyses_content else "(no previous analyses)"


async def get_injected_swe_runs(swe_run_ids: List[UUID]) -> str:
    swe_runs_content = []
    for swe_run_id in swe_run_ids:
        swe_result = await get_swe_result(swe_run_id)
        if swe_result:
            swe_runs_content.append(swe_result)

    return "\n\n".join(swe_runs_content) if swe_runs_content else "(no previous SWE runs)"


def print_message_history(messages: Sequence[ModelMessage], title: str = "Message History"):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

    for i, message in enumerate(messages):
        print(f"\n[Message {i}]")

        if isinstance(message, ModelRequest):
            print("  Type: ModelRequest")
            if hasattr(message, 'timestamp') and message.timestamp:
                print(f"  Timestamp: {message.timestamp}")

            print("  Parts:")
            for j, part in enumerate(message.parts):
                part_type = type(part).__name__
                print(f"    [{j}] {part_type}")

                if hasattr(part, 'timestamp') and part.timestamp:
                    print(f"         Timestamp: {part.timestamp}")

                if hasattr(part, 'content'):
                    content = str(part.content)
                    # Split by newlines and indent each line
                    lines = content.split('\n')
                    if len(lines) == 1:
                        print(f"         Content: {content}")
                    else:
                        print(f"         Content:")
                        for line in lines:
                            print(f"           {line}")

                if hasattr(part, 'tool_name'):
                    print(f"         Tool: {part.tool_name}")

                if hasattr(part, 'tool_call_id'):
                    print(f"         Tool Call ID: {part.tool_call_id}")

                if hasattr(part, 'id'):
                    print(f"         ID: {part.id}")

                if hasattr(part, 'provider_name'):
                    print(f"         Provider: {part.provider_name}")

        elif isinstance(message, ModelResponse):
            print("  Type: ModelResponse")
            if hasattr(message, 'timestamp') and message.timestamp:
                print(f"  Timestamp: {message.timestamp}")
            if hasattr(message, 'model_name') and message.model_name:
                print(f"  Model: {message.model_name}")
            if hasattr(message, 'provider_name') and message.provider_name:
                print(f"  Provider: {message.provider_name}")
            if hasattr(message, 'finish_reason') and message.finish_reason:
                print(f"  Finish Reason: {message.finish_reason}")

            print("  Parts:")
            for j, part in enumerate(message.parts):
                part_type = type(part).__name__
                print(f"    [{j}] {part_type}")

                if hasattr(part, 'content'):
                    content = str(part.content)
                    lines = content.split('\n')
                    if len(lines) == 1:
                        print(f"         Content: {content}")
                    else:
                        print(f"         Content:")
                        for line in lines:
                            print(f"           {line}")

                if hasattr(part, 'id'):
                    print(f"         ID: {part.id}")

                if hasattr(part, 'provider_name'):
                    print(f"         Provider: {part.provider_name}")

        else:
            print(f"  Type: {type(message).__name__}")
            print(f"  {message}")

    print("\n" + "=" * 80 + "\n")
