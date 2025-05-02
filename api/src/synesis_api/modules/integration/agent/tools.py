import time
import uuid
from datetime import datetime, timezone
from pydantic_ai import ModelRetry, RunContext
from synesis_api.utils import run_code_in_container
from synesis_api.modules.integration.agent.prompt import TIME_SERIES_TARGET_STRUCTURE
from synesis_api.modules.integration.agent.deps import IntegrationAgentDeps


async def get_target_structure(ctx: RunContext[IntegrationAgentDeps], data_modality: str):
    """
    Get the target output structure of the data.

    Args:
        ctx: The context
        data_modality: The modality of the data to get the structure for, one of ["time_series", "tabular", "image", "text"]
    """
    assert data_modality in ["time_series", "tabular", "image", "text"]

    message = {
        "id": str(uuid.uuid4()),
        "type": "tool_call",
        "role": "assistant",
        "content": f"Getting the target output structure of the {data_modality.replace('_', ' ')} data...",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await ctx.deps.redis_stream.xadd(str(ctx.deps.job_id), message)

    if data_modality == "time_series":
        return TIME_SERIES_TARGET_STRUCTURE
    else:
        raise ValueError(
            f"The target structure for {data_modality} data is not yet implemented.")


async def ping_human(ctx: RunContext[IntegrationAgentDeps], ping_timeout: float = 3):
    """
    Ping human. 

    Args:
        ctx: The context
        ping_timeout: The timeout for the ping.

    Returns:
        True if a human is listening, False otherwise.
    """
    ping_start_time = time.time()
    listening = False
    message = {
        "id": str(uuid.uuid4()),
        "type": "ping_human",
        "role": "assistant",
        "content": "Is a human listening?",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await ctx.deps.redis_stream.xadd(str(ctx.deps.job_id), message)
    response = await ctx.deps.redis_stream.xread({str(ctx.deps.job_id): "$"}, count=1, block=ping_timeout*1000)

    while response:
        last_id = response[0][1][-1][0]
        data = response[0][1][0][1]

        if data["type"] == "ping_human_response" and data["content"] == "listening":
            listening = True
            break

        response = await ctx.deps.redis_stream.xread({str(ctx.deps.job_id): last_id}, count=1)
        if ping_start_time + ping_timeout < time.time():
            break

    return listening


async def call_human_help(ctx: RunContext[IntegrationAgentDeps], help_message: str, ping_timeout: float = 3, response_timeout: float = 100):
    """
    Call human help. 

    Args:
        ctx: The context
        help_message: The message to send to the human.
        ping_timeout: The timeout for the ping.
        response_timeout: The timeout for the response.

    Returns:
        If a human is listening, the response from the human. Otherwise, a message indicating that no human is listening.
    """
    # Ping human

    listening = await ping_human(ctx, ping_timeout)

    if listening:
        start_time = time.time()
        message = {
            "id": str(uuid.uuid4()),
            "type": "help_call",
            "role": "assistant",
            "content": help_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await ctx.deps.redis_stream.xadd(str(ctx.deps.job_id), message)

        while True:
            if start_time + response_timeout < time.time():
                break

            response = await ctx.deps.redis_stream.xread({str(ctx.deps.job_id): last_id}, count=1)
            data = response[0][1][0][1]
            if data["type"] == "help_response":
                return data["content"]

            last_id = response[0][1][-1][0]

    return "No human listening. You can try to figure it out, or submit a paused response."


async def execute_python_code(ctx: RunContext[IntegrationAgentDeps], python_code: str, explanation: str):
    """
    Execute a python code block.

    Args:
        ctx: The context
        python_code: The python code to execute.
        explanation: Short explanation of the code and what you are trying to do.
    """

    message = {
        "id": str(uuid.uuid4()),
        "type": "tool_call",
        "role": "assistant",
        "content": explanation,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await ctx.deps.redis_stream.xadd(str(ctx.deps.job_id), message)

    out, err = await run_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out
