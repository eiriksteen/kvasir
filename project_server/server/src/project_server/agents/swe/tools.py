from pydantic_ai import RunContext, ModelRetry
from project_server.worker import logger
from typing import Literal, List

from project_server.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
)
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.entity_manager.data_source_manager import file_manager
from project_server.agents.runner_base import CodeForLog
from synesis_schemas.main_server import script_type_literal


swe_script_type_literal = Literal["function",
                                  "model",
                                  "pipeline",
                                  "data_integration"]


def _extract_injected_file_names(ctx: RunContext[SWEAgentDeps]) -> List[str]:
    return [f.filename for f in ctx.deps.functions_injected] + [m.filename for m in ctx.deps.models_injected]


def _has_version_suffix(file_name: str) -> bool:
    suffix = file_name.split("_")[-1][:-3]
    # return true if the suffix is v1, v2 .., v100, etc
    return suffix.startswith("v") and suffix[1:].isdigit()


def _save_script_with_version_handling(
        ctx: RunContext[SWEAgentDeps],
        file_name: str,
        script_content: str,
        script_type: swe_script_type_literal
):

    # Determine if this is the first modification of an input script
    injected_script_names = _extract_injected_file_names(ctx)
    if file_name in injected_script_names and file_name not in ctx.deps.modified_scripts_old_to_new_name:
        if not _has_version_suffix(file_name):
            raise ModelRetry(
                f"File name {file_name} needs version suffix to be updated. ")

        increase_version_number = True
    else:
        increase_version_number = False

    is_new_script = file_name not in ctx.deps.current_scripts
    if is_new_script:
        if _has_version_suffix(file_name):
            raise ModelRetry(
                f"File name {file_name} is a new script but already has a version suffix. The v1 suffix will be added automatically, do not include it in the file name. If you are trying to edit an existing script, use its current filename as input. ")

        add_uuid, add_v1 = True, True
    else:
        add_uuid, add_v1 = False, False

    # Save the script with appropriate version handling
    storage = file_manager.save_script(
        file_name,
        script_content,
        script_type,
        temporary=True,
        add_uuid=add_uuid,
        increase_version_number=increase_version_number,
        add_v1=add_v1
    )

    # Update context dependencies when version number increases
    if increase_version_number:
        ctx.deps.modified_scripts_old_to_new_name[file_name] = storage.filename
        ctx.deps.current_scripts.pop(file_name)

    if is_new_script:
        ctx.deps.new_scripts.add(storage.filename)

    ctx.deps.current_scripts[storage.filename] = script_content

    return storage


async def write_script(ctx: RunContext[SWEAgentDeps], script: str, file_name: str, script_type: script_type_literal) -> str:
    """
    Write a new script to a file. 
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        script: The script to write.
        file_name: The name of the new file to write the script to.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:
        str: The script with line numbers.
    """

    if not file_name.endswith(".py"):
        raise ModelRetry(
            f"File name must end with .py. Got: {file_name}")

    file_storage = _save_script_with_version_handling(
        ctx, file_name, script, script_type)

    script_with_line_numbers = add_line_numbers_to_script(script)
    out = f"NEW SCRIPT: \n\n <begin_script file_name={file_storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += f"You can now import it in your code from the module path: {file_storage.module_path}"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."
    out += f"\n\n The current scripts are: {list(ctx.deps.current_scripts.keys())}"

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=script, filename=file_storage.filename))

    return out


def read_script(ctx: RunContext[SWEAgentDeps], file_name: str) -> str:
    """
    Read a script from the current scripts.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {ctx.deps.current_scripts.keys()}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]
    script_with_line_numbers = add_line_numbers_to_script(script)
    out = f"READ SCRIPT: \n\n <begin_script file_name={file_name}>\n\n {script_with_line_numbers}\n\n <end_script>"

    return out


async def replace_script_lines(
    ctx: RunContext[SWEAgentDeps],
    file_name: str,
    script_type: script_type_literal,
    line_number_start: int,
    line_number_end: int,
    new_code: str
) -> str:
    """
    Replace lines in the current script with new code.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to modify. This line number is inclusive.
        line_number_end: The end line number of the code to modify. This line number is inclusive.
        new_code: The new code to replace the old code at the given line numbers. Remember indents if adding lines inside functions or classes!
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    updated_script = replace_lines_in_script(
        script,
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=False
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.\n"
    out += "Note that the version number may have increased in case of updates. "

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=updated_script, filename=storage.filename))

    return out


async def add_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, new_code: str, start_line: int) -> str:
    """
    Add lines to the current script at the given line number.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        new_code: The new code to add. Remember indents if adding lines inside functions or classes!
        start_line: The line number to add the lines at. This line number is inclusive.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    updated_script = add_lines_to_script_at_line(
        script,
        new_code,
        start_line,
        script_has_line_numbers=False
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=updated_script, filename=storage.filename))

    return out


async def delete_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, line_number_start: int, line_number_end: int) -> str:
    """
    Delete lines from the current script at the given line numbers.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to delete. This line number is inclusive.
        line_number_end: The end line number of the code to delete. This line number is inclusive.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:    
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    updated_script = delete_lines_from_script(
        script,
        line_number_start,
        line_number_end,
        script_has_line_numbers=False
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    if ctx.deps.log_code:
        await ctx.deps.log_code(
            CodeForLog(code=updated_script, filename=storage.filename))

    return out
