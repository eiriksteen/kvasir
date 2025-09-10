import ast
from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_shell_code_in_container, remove_line_numbers_from_script, run_python_code_in_container


class PlanningOutput(BaseModel):
    plan: str


class SetupAgentOutput(BaseModel):
    dependencies: List[str]
    python_version: str


class SetupAgentOutputWithScript(SetupAgentOutput):
    script: str


class ConfigOutput(BaseModel):
    config_dict: dict


class ImplementationOutput(BaseModel):
    code_explanation: str


class ImplementationOutputFull(ImplementationOutput):
    script: str
    args_ordered: List[str]
    run_output: str


class SWEAgentOutput(BaseModel):
    implementation: ImplementationOutputFull
    setup: Optional[SetupAgentOutputWithScript] = None
    config: Optional[ConfigOutput] = None
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
    if not ctx.deps.current_scripts[ctx.deps.current_file_name]:
        raise ModelRetry("No script written")

    if ctx.deps.current_file_name != "setup.sh":
        raise ModelRetry(
            f"The current script is not the setup script, it must be named 'setup.sh'! The current script is {ctx.deps.current_file_name}")

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

    script = remove_line_numbers_from_script(
        ctx.deps.current_scripts[ctx.deps.current_file_name])

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


async def submit_implementation_output(ctx: RunContext[SWEAgentDeps], result: ImplementationOutput) -> ImplementationOutputFull:

    if not ctx.deps.current_file_name or not ctx.deps.current_scripts[ctx.deps.current_file_name]:
        raise ModelRetry("No script written")

    if ctx.deps.current_file_name != "implementation.py":
        raise ModelRetry(
            f"The current script is not the implementation script, it must be named 'implementation.py'! The current script is {ctx.deps.current_file_name}")

    script = remove_line_numbers_from_script(
        ctx.deps.current_scripts[ctx.deps.current_file_name])

    try:
        fn_named_run_found = False
        for node in ast.walk(ast.parse(script)):
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                args = [arg.arg for arg in node.args.args]
                fn_named_run_found = True
                break
    except Exception as e:
        raise ModelRetry(
            f"Error parsing the implementation script: {e}")

    if not fn_named_run_found:
        raise ModelRetry(
            "No function named 'run' found in the implementation script")

    script_to_run = script
    if ctx.deps.test_code_to_append_to_implementation:
        script_to_run = f"{script}\n\n{ctx.deps.test_code_to_append_to_implementation}"

    out, err = await run_python_code_in_container(script_to_run, container_name=ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return ImplementationOutputFull(**result.model_dump(), script=script, args_ordered=args, run_output=out)
