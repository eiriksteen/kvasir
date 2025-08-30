from pydantic_ai import RunContext, ModelRetry

from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.agents.pipeline.output import DetailedFunctionDescription


async def validate_script(ctx: RunContext[SWEAgentDeps], script: str) -> bool:
    """
    Validate the implementation of a function.
    """

    # TODO: Implement

    return True


async def validate_arg_order(ctx: RunContext[SWEAgentDeps], script: str) -> bool:
    """
    Validate the argument order of a function.
    """

    # TODO: Implement

    return True
