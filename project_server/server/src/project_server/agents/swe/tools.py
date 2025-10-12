from pydantic_ai import RunContext, ModelRetry
from typing import Literal

from project_server.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
    remove_line_numbers_from_script,
)
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.entity_manager.file_manager import file_manager
from project_server.worker import logger


script_type_literal = Literal["function",
                              "model",
                              "pipeline",
                              "data_integration"]


def _save_script_with_version_handling(
        ctx: RunContext[SWEAgentDeps],
        file_name: str,
        script_content: str,
        script_type: script_type_literal):

    # Determine if this is the first modification of an input script
    if file_name in ctx.deps.input_scripts and file_name not in ctx.deps.modified_scripts_old_to_new_name:
        increase_version_number = True
    else:
        increase_version_number = False

    # Save the script with appropriate version handling
    storage = file_manager.save_script(
        file_name,
        script_content,
        script_type,
        temporary=True,
        add_uuid=False,
        increase_version_number=increase_version_number
    )

    # Update context dependencies when version number increases
    if increase_version_number:
        ctx.deps.modified_scripts_old_to_new_name[file_name] = storage.filename
        ctx.deps.current_scripts.pop(file_name)

    logger.info(
        f"CURRENT SCRIPT NAMES ARE: {list(ctx.deps.current_scripts.keys())}")

    return storage


def write_script(ctx: RunContext[SWEAgentDeps], script: str, file_name: str, script_type: script_type_literal) -> str:
    """
    Write a new script to a file. 
    An UUID will be prepended to the filename to ensure it is unique. 
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        script: The script to write.
        file_name: The name of the new file to write the script to.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The script with line numbers.
    """

    if not file_name.endswith(".py"):
        raise ModelRetry(
            f"File name must end with .py. Got: {file_name}")

    if "v1" in file_name:
        raise ModelRetry(
            f"File name must not contain v1. Will be added automatically.")

    updated_script = add_line_numbers_to_script(script)
    file_storage = file_manager.save_script(
        file_name, script, script_type, add_uuid=True, temporary=True, add_v1=True)

    ctx.deps.new_scripts.add(file_storage.filename)
    ctx.deps.current_scripts[file_storage.filename] = updated_script

    out = f"NEW SCRIPT: \n\n <begin_script file_name={file_name}>\n\n {updated_script}\n\n <end_script>"
    out += f"You can now import it in your code from the module path: {file_storage.module_path}"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."
    out += f"\n\n The current scripts are: {list(ctx.deps.current_scripts.keys())}"

    return out


def read_script(ctx: RunContext[SWEAgentDeps], file_name: str) -> str:
    """
    Read a script from the current scripts.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    out = f"READ SCRIPT: \n\n <begin_script file_name={file_name}>\n\n {ctx.deps.current_scripts[file_name]}\n\n <end_script>"
    return out


def replace_script_lines(
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
        script_has_line_numbers=True
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        remove_line_numbers_from_script(updated_script),
        script_type
    )

    ctx.deps.current_scripts[storage.filename] = updated_script

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {updated_script}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.\n"
    out += "Note that the version number may have increased in case of updates. "

    return out


def add_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, new_code: str, start_line: int) -> str:
    """
    Add lines to the current script at the given line number.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        new_code: The new code to add. Remember indents if adding lines inside functions or classes!
        start_line: The line number to add the lines at. This line number is inclusive.
        reasoning: The concise reasoning for why you are calling this tool.

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
        script_has_line_numbers=True
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        remove_line_numbers_from_script(updated_script),
        script_type
    )

    ctx.deps.current_scripts[storage.filename] = updated_script

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {updated_script}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def delete_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, line_number_start: int, line_number_end: int) -> str:
    """
    Delete lines from the current script at the given line numbers.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to delete. This line number is inclusive.
        line_number_end: The end line number of the code to delete. This line number is inclusive.
        reasoning: The concise reasoning for why you are calling this tool.

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
        script_has_line_numbers=True
    )

    storage = _save_script_with_version_handling(
        ctx,
        file_name,
        remove_line_numbers_from_script(updated_script),
        script_type
    )

    ctx.deps.current_scripts[storage.filename] = updated_script

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {updated_script}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out
