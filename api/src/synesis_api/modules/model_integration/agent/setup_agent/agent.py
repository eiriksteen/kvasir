from pydantic_ai import Agent, RunContext, ModelRetry
from dataclasses import dataclass
from typing import List
from synesis_api.base_schema import BaseSchema
from synesis_api.utils import (
    get_model,
    run_shell_code_in_container,
    remove_line_numbers_from_script
)
from synesis_api.modules.model_integration.agent.setup_agent.prompt import SETUP_SYSTEM_PROMPT
from synesis_api.modules.model_integration.agent.shared_tools import (
    get_repo_info,
    get_repo_structure,
    get_file_content,
    write_script,
    replace_script_lines,
    add_script_lines,
    delete_script_lines
)
from synesis_api.modules.model_integration.agent.prepare_tools import filter_tools_by_source
from synesis_api.modules.model_integration.agent.base_deps import BaseDeps
from synesis_api.modules.model_integration.agent.history_processors import keep_only_most_recent_script, summarize_message_history


@dataclass(kw_only=True)
class SetupDeps(BaseDeps):
    run_pylint: bool = False
    pass


class SetupAgentOutput(BaseSchema):
    dependencies: List[str]
    python_version: str


class SetupAgentOutputWithScript(SetupAgentOutput):
    script: str


model = get_model()

setup_agent = Agent(
    model,
    deps_type=SetupDeps,
    output_type=SetupAgentOutput,
    tools=[
        get_repo_info,
        get_repo_structure,
        get_file_content,
        write_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines
    ],
    prepare_tools=filter_tools_by_source,
    retries=5,
    history_processors=[keep_only_most_recent_script,
                        summarize_message_history]
)


@setup_agent.system_prompt
def get_setup_system_prompt(ctx: RunContext[SetupDeps]) -> str:

    if ctx.deps.source == "github":
        return f"{SETUP_SYSTEM_PROMPT}\n\n GITHUB URL: {ctx.deps.model_id}"
    elif ctx.deps.source == "pip":
        return f"{SETUP_SYSTEM_PROMPT}\n\n PIP PACKAGE: {ctx.deps.model_id}"


@setup_agent.output_validator
async def validate_setup_output(
    ctx: RunContext[SetupDeps],
    result: SetupAgentOutput
) -> SetupAgentOutputWithScript:
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

    print("@"*20, "TESTING SETUP SCRIPT", "@"*20)
    print(f"Python version: {result.python_version}")
    print("@"*50)

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
            print("@"*20, "ERROR INSTALLING PYTHON VERSION", "@"*20)
            print(f"Error: {err}")
            print("@"*50)
            raise ModelRetry(f"Error installing python version: {err}")

    _, err = await run_shell_code_in_container(
        f"pyenv global {result.python_version}",
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        print("@"*20, "ERROR SETTING GLOBAL PYTHON VERSION", "@"*20)
        print(f"Error: {err}")
        print("@"*50)
        raise ModelRetry(f"Error setting global python version: {err}")

    script = remove_line_numbers_from_script(ctx.deps.current_script)

    print("RAW SCRIPT WITHOUT LINE NUMBERS")
    print(script)
    print("@"*50)

    _, err = await run_shell_code_in_container(
        script,
        container_name=ctx.deps.container_name,
        cwd=ctx.deps.cwd
    )

    if err:
        print("@"*20, "ERROR EXECUTING SETUP SCRIPT", "@"*20)
        print(f"Error: {err}")
        print("@"*50)

        error_message = f"Error executing setup script: {err}"
        if ctx.retry > 3:
            error_message = f"{error_message}\n\n" \
                "Remember, if you are facing package installation and dependency issues, " \
                "install the latest stable versions of Python and all dependencies (the default versions)!"

        raise ModelRetry(error_message)

    print("Setup script executed successfully")

    return SetupAgentOutputWithScript(
        **result.model_dump(),
        script=script
    )
