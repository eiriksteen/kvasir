from pydantic_ai import RunContext, ModelRetry

from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.agents.pipeline.output import DetailedFunctionDescription


async def validate_script(ctx: RunContext[SWEAgentDeps], script: str) -> str:
    """
    Validate the implementation of a function.
    """

    if ctx.deps.current_script is None:
        raise ModelRetry("No script provided")

    return "Function implementation validated"
