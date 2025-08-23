from typing import List, Optional
from pydantic_ai import RunContext, ModelRetry

from synesis_api.base_schema import BaseSchema
from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.utils.code_utils import run_shell_code_in_container, remove_line_numbers_from_script, run_python_code_in_container


class PlanningOutput(BaseSchema):
    plan: str


class SetupAgentOutput(BaseSchema):
    dependencies: List[str]
    python_version: str


class SetupAgentOutputWithScript(SetupAgentOutput):
    script: str


class ImplementationOutput(BaseSchema):
    code_explanation: str


class ImplementationOutputWithScript(ImplementationOutput):
    script: str


class SWEAgentOutput(BaseSchema):
    setup: SetupAgentOutputWithScript
    implementation: ImplementationOutputWithScript
    plan: Optional[PlanningOutput] = None


async def submit_setup_output(ctx: RunContext[SWEAgentDeps], result: SetupAgentOutput) -> SetupAgentOutputWithScript:
    """
    Validate and execute the setup script.

    Args:
        ctx: The context.
        result: The setup output.

    Returns:
        SetupOutput: The setup output.
    """
    if not ctx.deps.current_script:
        raise ModelRetry("No script written")

    check_output, _ = await run_shell_code_in_container(
        f"pyenv versions | grep {result.python_version}",
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if not check_output.strip():
        _, err = await run_shell_code_in_container(
            f"pyenv install {result.python_version}",
            container_name=ctx.deps.container_name,
            cwd=ctx.deps.cwd
        )

        if err:
            raise ModelRetry(f"Error installing python version: {err}")

    _, err = await run_shell_code_in_container(
        f"pyenv global {result.python_version}",
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        raise ModelRetry(f"Error setting global python version: {err}")

    script = remove_line_numbers_from_script(ctx.deps.current_script)

    if not script.strip().startswith('#!/bin/bash') and not script.strip().startswith('#!/usr/bin/env bash'):
        raise ModelRetry(
            "Setup script must be a bash script! Start with '#!/bin/bash' or '#!/usr/bin/env bash'")

    _, err = await run_shell_code_in_container(
        script,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        error_message = f"Error executing setup script: {err}"
        if ctx.retry > 3:
            error_message = f"{error_message}\n\n" \
                "Remember, if you are facing package installation and dependency issues, " \
                "install the latest stable versions of Python and all dependencies (the default versions)!"

        raise ModelRetry(error_message)

    return SetupAgentOutputWithScript(
        **result.model_dump(),
        script=script
    )


async def submit_implementation_output(ctx: RunContext[SWEAgentDeps], result: ImplementationOutput) -> ImplementationOutputWithScript:

    if not ctx.deps.current_script:
        raise ModelRetry("No script written")

    script = remove_line_numbers_from_script(ctx.deps.current_script)

    for func in ctx.deps.implementation_validation_fns:
        result = await func(ctx, script)

    return ImplementationOutputWithScript(**result.model_dump(), script=script)
