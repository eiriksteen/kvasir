from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_shell_code_in_container, remove_line_numbers_from_script, run_python_code_in_container
from project_server.agents.runner_base import CodeForLog
from synesis_schemas.main_server import script_type_literal

from project_server.worker import logger


class SetupAgentOutput(BaseModel):
    dependencies: List[str]
    python_version: str


class SetupAgentOutputWithScript(SetupAgentOutput):
    script: str


class ImplementationOutput(BaseModel):
    code_explanation: str


class NewScriptOutput(BaseModel):
    filename: str
    script: str


class ModifiedScriptOutput(BaseModel):
    original_filename: str
    new_filename: str
    original_script: str
    new_script: str
    type: script_type_literal


class ImplementationOutputFull(ImplementationOutput):
    main_script: NewScriptOutput
    run_output: str
    new_scripts: List[NewScriptOutput] = []
    modified_scripts: List[ModifiedScriptOutput] = []


class SWEAgentOutput(BaseModel):
    implementation: ImplementationOutputFull
    setup: Optional[SetupAgentOutputWithScript] = None


async def submit_setup_output(ctx: RunContext[SWEAgentDeps], file_name: str, result: SetupAgentOutput) -> SetupAgentOutputWithScript:
    """
    Validate and execute the setup script.

    Args:
        ctx: The context.
        result: The setup output.

    Returns:
        SetupOutput: The setup output.
    """
    if file_name not in ctx.deps.current_scripts:
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
    script_with_test_code = f"{script}\n\n{ctx.deps.test_code_to_append_to_implementation}" if ctx.deps.test_code_to_append_to_implementation else script

    logger.info("CURRENT SCRIPTS")
    logger.info(ctx.deps.current_scripts.keys())
    logger.info("RUNNING CODE")
    logger.info(script_with_test_code)

    out, err = await run_python_code_in_container(script_with_test_code, container_name=ctx.deps.container_name)

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=script_with_test_code,
            filename=file_name,
            output=out,
            error=err
        ))

    if err:
        logger.info(f"Error executing code: {err}")
        raise ModelRetry(f"Error executing code: {err}")

    new_scripts = []
    if ctx.deps.new_scripts:
        for new_script_name in ctx.deps.new_scripts:
            new_script = ctx.deps.current_scripts[new_script_name]
            new_scripts.append(NewScriptOutput(
                filename=new_script_name, script=new_script))

    modified_scripts = []
    if ctx.deps.modified_scripts_old_to_new_name:
        for original_script_name, new_script_name in ctx.deps.modified_scripts_old_to_new_name.items():

            original_fn = next(
                (f for f in ctx.deps.functions_injected if f.filename == original_script_name), None)
            original_mdl = next(
                (m for m in ctx.deps.models_injected if m.filename == original_script_name), None)

            if original_fn:
                with open(original_fn.script_path, "r") as f:
                    original_script = f.read()
            elif original_mdl:
                with open(original_mdl.script_path, "r") as f:
                    original_script = f.read()
            else:
                raise RuntimeError(
                    f"Original script {original_script_name} which has been modified not found in injected functions or models")

            script_type = "model" if original_mdl else "function"

            modified_script = ctx.deps.current_scripts[new_script_name]
            modified_scripts.append(ModifiedScriptOutput(
                original_filename=original_script_name,
                new_filename=new_script_name,
                original_script=original_script,
                new_script=modified_script,
                type=script_type
            ))

    main_script = NewScriptOutput(filename=file_name, script=script)

    return ImplementationOutputFull(**result.model_dump(), main_script=main_script, run_output=out, modified_scripts=modified_scripts, new_scripts=new_scripts)
