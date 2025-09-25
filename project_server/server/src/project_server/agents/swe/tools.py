from pydantic_ai import RunContext, ModelRetry

from project_server.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
    run_pylint
)
from project_server.agents.swe.deps import SWEAgentDeps


def write_script(ctx: RunContext[SWEAgentDeps], script: str, file_name: str) -> str:
    """
    Write a new script to a file. 
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        script: The script to write.
        file_name: The name of the new file to write the script to.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The script with line numbers.
    """

    ctx.deps.current_file_name = file_name
    ctx.deps.current_scripts[file_name] = add_line_numbers_to_script(script)

    out = f"NEW SCRIPT: \n\n <begin_script file_name={ctx.deps.current_file_name}>\n\n {ctx.deps.current_scripts[file_name]}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(ctx.deps.current_scripts[file_name])
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."
    out += f"\n\n The current script is {ctx.deps.current_file_name}. To switch scripts, call the switch_script tool."

    return out


def switch_script(ctx: RunContext[SWEAgentDeps], file_name: str) -> str:
    """
    Switch to a different script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    ctx.deps.current_file_name = file_name
    return f"SWITCHED TO SCRIPT: \n\n <begin_script file_name={ctx.deps.current_file_name}>\n\n {ctx.deps.current_scripts[file_name]}\n\n <end_script>"


def replace_script_lines(ctx: RunContext[SWEAgentDeps], line_number_start: int, line_number_end: int, new_code: str) -> str:
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
    if not ctx.deps.current_scripts[ctx.deps.current_file_name]:
        return "No script to modify"

    ctx.deps.current_scripts[ctx.deps.current_file_name] = replace_lines_in_script(
        ctx.deps.current_scripts[ctx.deps.current_file_name],
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=True
    )

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={ctx.deps.current_file_name}>\n\n {ctx.deps.current_scripts[ctx.deps.current_file_name]}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(
            ctx.deps.current_scripts[ctx.deps.current_file_name])
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def add_script_lines(ctx: RunContext[SWEAgentDeps], new_code: str, start_line: int) -> str:
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
    if not ctx.deps.current_scripts[ctx.deps.current_file_name]:
        return "No script to modify"

    ctx.deps.current_scripts[ctx.deps.current_file_name] = add_lines_to_script_at_line(
        ctx.deps.current_scripts[ctx.deps.current_file_name],
        new_code,
        start_line,
        script_has_line_numbers=True
    )

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={ctx.deps.current_file_name}>\n\n {ctx.deps.current_scripts[ctx.deps.current_file_name]}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(
            ctx.deps.current_scripts[ctx.deps.current_file_name])
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def delete_script_lines(ctx: RunContext[SWEAgentDeps], line_number_start: int, line_number_end: int) -> str:
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
    if not ctx.deps.current_scripts[ctx.deps.current_file_name]:
        return "No script to modify"

    ctx.deps.current_scripts[ctx.deps.current_file_name] = delete_lines_from_script(
        ctx.deps.current_scripts[ctx.deps.current_file_name],
        line_number_start,
        line_number_end,
        script_has_line_numbers=True
    )

    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={ctx.deps.current_file_name}>\n\n {ctx.deps.current_scripts[ctx.deps.current_file_name]}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(
            ctx.deps.current_scripts[ctx.deps.current_file_name])
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out
