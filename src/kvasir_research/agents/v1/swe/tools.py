from pathlib import Path
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from kvasir_research.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script
)
from kvasir_research.agents.v1.swe.deps import SWEDeps


async def write_script(ctx: RunContext[SWEDeps], file_path: str, content: str) -> str:
    """
    Write a new script to a file. 
    This is only for creating new scripts. To modify existing scripts, use add_script_lines, replace_script_lines, or delete_script_lines instead.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        file_path: The path to the file to write the content to (including the file name). Will be run from the cwd. Accepts absolute or relative paths. 
        content: The content to write to the file.

    Returns:
        str: The script with line numbers.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Writing new file: {file_path} ({len(content)} characters)", "tool_call")

    if not _validate_path_permissions(ctx, file_path):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if await ctx.deps.sandbox.check_file_exists(file_path):
        raise ModelRetry(
            f"File {file_path} already exists. To modify an existing file, use add_script_lines, replace_script_lines, or delete_script_lines instead. write_script is only for creating new files.")

    await ctx.deps.sandbox.write_file(file_path, content)

    # Track the modified file
    ctx.deps.modified_files[file_path] = content

    content_with_line_numbers = add_line_numbers_to_script(content)

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created file: {file_path}", "result")

    return f"WROTE TO FILE: {file_path}\n\n<file path={file_path}>\n\n{content_with_line_numbers}\n\n</file>"


async def replace_script_lines(
    ctx: RunContext[SWEDeps],
    file_path: str,
    line_number_start: int,
    line_number_end: int,
    new_code: str
) -> str:
    """
    Replace lines in the current file with new code.
    The file is not automatically run and validated, you must call the final_result tool to submit the file for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to modify. This line number is inclusive.
        line_number_end: The end line number of the code to modify. This line number is inclusive.
        new_code: The new code to replace the old code at the given line numbers. Remember indents if adding lines inside functions or classes!
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The updated script.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Replacing lines {line_number_start}-{line_number_end} in {file_path} ({len(new_code)} characters)", "tool_call")

    if not _validate_path_permissions(ctx, file_path):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if not await ctx.deps.sandbox.check_file_exists(file_path):
        raise ModelRetry(
            f"File {file_path} does not exist. To create a new file, call the write_file tool.")

    old_content = await ctx.deps.sandbox.read_file(file_path)

    updated_content = replace_lines_in_script(
        old_content,
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=False
    )

    await ctx.deps.sandbox.write_file(file_path, updated_content)

    # Track the modified file
    ctx.deps.modified_files[file_path] = updated_content

    updated_content_with_line_numbers = add_line_numbers_to_script(
        updated_content)
    out = f"UPDATED FILE: {file_path}\n\n <file path={file_path}>\n\n {updated_content_with_line_numbers}\n\n </file>"
    out += "\n\nThe file is not automatically run and validated, you must call the final_result tool to submit the file for validation and feedback.\n"

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Replaced lines {line_number_start}-{line_number_end} in {file_path}", "result")

    return out


async def add_script_lines(ctx: RunContext[SWEDeps], file_path: str, new_code: str, start_line: int) -> str:
    """
    Add lines to the current script at the given line number.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        new_code: The new code to add. Remember indents if adding lines inside functions or classes!
        start_line: The line number to add the lines at. This line number is inclusive.

    Returns:
        str: The updated script.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Adding lines at line {start_line} in {file_path} ({len(new_code)} characters)", "tool_call")

    if not _validate_path_permissions(ctx, file_path):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if not await ctx.deps.sandbox.check_file_exists(file_path):
        raise ModelRetry(
            f"Script {file_path} does not exist. To create a new script, call the write_file tool.")

    old_content = await ctx.deps.sandbox.read_file(file_path)

    updated_content = add_lines_to_script_at_line(
        old_content,
        new_code,
        start_line,
        script_has_line_numbers=False
    )

    await ctx.deps.sandbox.write_file(file_path, updated_content)

    # Track the modified file
    ctx.deps.modified_files[file_path] = updated_content

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <file path={file_path}>\n\n {script_with_line_numbers}\n\n </file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Added lines at line {start_line} in {file_path}", "result")

    return out


async def delete_script_lines(ctx: RunContext[SWEDeps], file_path: str, line_number_start: int, line_number_end: int) -> str:
    """
    Delete lines from the current script at the given line numbers.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to delete. This line number is inclusive.
        line_number_end: The end line number of the code to delete. This line number is inclusive.

    Returns:    
        str: The updated script.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleting lines {line_number_start}-{line_number_end} from {file_path}", "tool_call")

    if not _validate_path_permissions(ctx, file_path):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if not await ctx.deps.sandbox.check_file_exists(file_path):
        raise ModelRetry(
            f"File {file_path} does not exist. To create a new file, call the write_file tool.")

    old_content = await ctx.deps.sandbox.read_file(file_path)

    updated_content = delete_lines_from_script(
        old_content,
        line_number_start,
        line_number_end,
        script_has_line_numbers=False
    )

    await ctx.deps.sandbox.write_file(file_path, updated_content)

    # Track the modified file
    ctx.deps.modified_files[file_path] = updated_content

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <file path={file_path}>\n\n {script_with_line_numbers}\n\n </file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleted lines {line_number_start}-{line_number_end} from {file_path}", "result")

    return out


async def delete_file(ctx: RunContext[SWEDeps], file_path: str) -> str:
    """
    Delete a file from the project.
    This permanently removes the file. Use with caution.

    Args:
        ctx: The context.
        file_path: The path of the file to delete.

    Returns:
        str: Confirmation message.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleting file: {file_path}", "tool_call")

    if not _validate_path_permissions(ctx, file_path):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if not await ctx.deps.sandbox.check_file_exists(file_path):
        raise ModelRetry(f"File {file_path} does not exist.")

    await ctx.deps.sandbox.delete_file(file_path)

    # Remove from modified_files tracking if it was there
    if file_path in ctx.deps.modified_files:
        del ctx.deps.modified_files[file_path]

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleted file: {file_path}", "result")

    return f"Successfully deleted {file_path}"


swe_toolset = FunctionToolset(
    tools=[
        write_script,
        replace_script_lines,
        add_script_lines,
        delete_script_lines,
        delete_file
    ],
    max_retries=3
)


##


def _validate_path_permissions(ctx: RunContext[SWEDeps], path: str | Path) -> bool:
    path = Path(path).resolve()

    # Check if path is in any read-only path
    for read_only_path in ctx.deps.read_only_paths:
        if ctx.deps.sandbox.is_subpath(path, Path(read_only_path).resolve()):
            return False

    return True
