from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_shell_code_in_container, remove_line_numbers_from_script, run_python_code_in_container
from project_server.worker import logger


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
    main_script_filename: str
    code_explanation: str


class NewScriptOutput(BaseModel):
    filename: str
    script: str


class ModifiedScriptOutput(BaseModel):
    filename: str
    original_script: str
    new_script: str


class ImplementationOutputFull(ImplementationOutput):
    main_script: str
    run_output: str
    modified_scripts: List[ModifiedScriptOutput] = []
    new_scripts: List[NewScriptOutput] = []


class SWEAgentOutput(BaseModel):
    implementation: ImplementationOutputFull
    setup: Optional[SetupAgentOutputWithScript] = None
    config: Optional[ConfigOutput] = None
    plan: Optional[PlanningOutput] = None


async def submit_setup_output(ctx: RunContext[SWEAgentDeps], file_name: str, result: SetupAgentOutput) -> SetupAgentOutputWithScript:
    """
    Validate and execute the setup script.

    Args:
        ctx: The context.
        result: The setup output.

    Returns:
        SetupOutput: The setup output.
    """
    if not ctx.deps.current_scripts[file_name]:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

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

    script = remove_line_numbers_from_script(script)

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


async def submit_implementation_output(ctx: RunContext[SWEAgentDeps], file_name: str, result: ImplementationOutput) -> ImplementationOutputFull:

    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    if not script:
        raise ModelRetry("No script written")

    script = remove_line_numbers_from_script(script)
    script_with_test_code = f"{script}\n\n{ctx.deps.test_code_to_append_to_implementation}" if ctx.deps.test_code_to_append_to_implementation else script

    if ctx.deps.log:
        logger.info(
            f"Running code to validate implementation:\n\n {script_with_test_code}")

    out, err = await run_python_code_in_container(script_with_test_code, container_name=ctx.deps.container_name)

    if ctx.deps.log:
        logger.info(f"Code execution output:\n\n {out}")
        logger.info(f"Code execution error:\n\n {err}")

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    new_scripts = []
    if ctx.deps.new_scripts:
        for new_script_name in ctx.deps.new_scripts:
            new_script = ctx.deps.current_scripts[new_script_name]
            new_scripts.append(NewScriptOutput(
                filename=new_script_name, script=new_script))

    modified_scripts = []
    if ctx.deps.input_scripts and ctx.deps.modified_scripts:
        for modified_script_name in ctx.deps.modified_scripts:
            if modified_script_name in ctx.deps.input_scripts:
                original_script = ctx.deps.input_scripts[modified_script_name]
                modified_script = ctx.deps.current_scripts[modified_script_name]
                modified_scripts.append(ModifiedScriptOutput(
                    filename=modified_script_name,
                    original_script=original_script,
                    new_script=modified_script
                ))

    return ImplementationOutputFull(**result.model_dump(), main_script=script, run_output=out, modified_scripts=modified_scripts, new_scripts=new_scripts)
