from pathlib import Path
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from project_server.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
    filter_content_by_extension,
)
from project_server.agents.swe.deps import SWEAgentDeps, RenamedFile
from project_server.utils.docker_utils import (
    write_file_to_container,
    read_file_from_container,
    remove_from_container,
    rename_in_container,
    check_file_exists_in_container
)
from synesis_schemas.project_server import FileInRun


def _update_modified_files_state(
        ctx: RunContext[SWEAgentDeps],
        file_path: str,
        new_content: str,
        old_content: str) -> None:

    is_in_new = any(f.path == file_path for f in ctx.deps.new_files)

    # Filter content for non-readable files
    filtered_new_content = filter_content_by_extension(file_path, new_content)
    filtered_old_content = filter_content_by_extension(file_path, old_content)

    if is_in_new:
        new_version = FileInRun(path=file_path, content=filtered_new_content)
        ctx.deps.new_files = [
            f for f in ctx.deps.new_files if f.path != file_path] + [new_version]
    else:
        old_version = next(
            (f for f in ctx.deps.modified_files if f.path == str(file_path)), None)
        # Only put old content on the very first modification
        if old_version:
            # Preserve the original old_content if it exists, otherwise use content
            original_content = old_version.old_content
            new_version = FileInRun(
                path=str(file_path), content=filtered_new_content, old_content=original_content)
        else:
            new_version = FileInRun(
                path=str(file_path), content=filtered_new_content, old_content=filtered_old_content)

        ctx.deps.modified_files = [
            f for f in ctx.deps.modified_files if f.path != str(file_path)] + [new_version]


async def write_file(ctx: RunContext[SWEAgentDeps], content: str, file_path: str) -> str:
    """
    Write a new script to a file. 
    This is only for creating new files. To modify existing files, use add_file_lines, replace_file_lines, or delete_file_lines instead.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        content: The content to write to the file.
        file_path: The path to the file to write the content to (including the file name). Will be run from the cwd. Accepts absolute or relative paths. 

    Returns:
        str: The script with line numbers.
    """

    file_path = Path(file_path)

    if await check_file_exists_in_container(file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"File {file_path} already exists. To modify an existing file, use add_file_lines, replace_file_lines, or delete_file_lines instead. write_file is only for creating new files.")

    await write_file_to_container(
        file_path,
        content,
        ctx.deps.container_name
    )

    filtered_content = filter_content_by_extension(file_path, content)
    ctx.deps.new_files.append(
        FileInRun(path=str(file_path), content=filtered_content))

    content_with_line_numbers = add_line_numbers_to_script(content)

    return f"WROTE TO FILE: {file_path}\n\n<begin_file file_path={file_path}>\n\n{content_with_line_numbers}\n\n<end_file>"


async def replace_file_lines(
    ctx: RunContext[SWEAgentDeps],
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
    file_path = Path(file_path)

    if not await check_file_exists_in_container(file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"File {file_path} does not exist. To create a new file, call the write_file tool.")

    old_content = await read_file_from_container(
        file_path,
        ctx.deps.container_name
    )

    updated_content = replace_lines_in_script(
        old_content,
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=False
    )

    await write_file_to_container(
        file_path,
        updated_content,
        ctx.deps.container_name
    )

    _update_modified_files_state(
        ctx, str(file_path), updated_content, old_content)

    updated_content_with_line_numbers = add_line_numbers_to_script(
        updated_content)
    out = f"UPDATED FILE: {file_path}\n\n <begin_file file_path={file_path}>\n\n {updated_content_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe file is not automatically run and validated, you must call the final_result tool to submit the file for validation and feedback.\n"

    return out


async def add_file_lines(ctx: RunContext[SWEAgentDeps], file_name: str, new_code: str, start_line: int) -> str:
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
    file_path = Path(file_name)
    if not await check_file_exists_in_container(file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"Script {file_name} does not exist. To create a new script, call the write_file tool.")

    old_content = await read_file_from_container(
        file_path,
        ctx.deps.container_name
    )

    updated_content = add_lines_to_script_at_line(
        old_content,
        new_code,
        start_line,
        script_has_line_numbers=False
    )

    await write_file_to_container(
        file_path,
        updated_content,
        ctx.deps.container_name
    )

    _update_modified_files_state(
        ctx, str(file_path), updated_content, old_content)

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <begin_file file_path={file_path}>\n\n {script_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


async def delete_file_lines(ctx: RunContext[SWEAgentDeps], file_path: str, line_number_start: int, line_number_end: int) -> str:
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
    file_path = Path(file_path)

    if not await check_file_exists_in_container(file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"File {file_path} does not exist. To create a new file, call the write_file tool.")

    old_content = await read_file_from_container(
        file_path,
        ctx.deps.container_name
    )

    updated_content = delete_lines_from_script(
        old_content,
        line_number_start,
        line_number_end,
        script_has_line_numbers=False
    )

    await write_file_to_container(
        file_path,
        updated_content,
        ctx.deps.container_name
    )

    _update_modified_files_state(
        ctx, str(file_path), updated_content, old_content)

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <begin_file file_path={file_path}>\n\n {script_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


async def rename_file(ctx: RunContext[SWEAgentDeps], old_path: str, new_path: str) -> str:
    """
    Rename or move a file to a new location.
    This can be used to rename files or move them to different directories.

    Args:
        ctx: The context.
        old_path: The current path of the file to rename/move.
        new_path: The new path for the file.

    Returns:
        str: Confirmation message.
    """
    old_file_path = Path(old_path)
    new_file_path = Path(new_path)

    if not await check_file_exists_in_container(old_file_path, ctx.deps.container_name):
        raise ModelRetry(f"File {old_path} does not exist.")

    if await check_file_exists_in_container(new_file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"File {new_path} already exists. Cannot rename to an existing file.")

    # Read the content before renaming for revert purposes
    file_content = await read_file_from_container(old_file_path, ctx.deps.container_name)
    content = filter_content_by_extension(old_file_path, file_content)

    _, err = await rename_in_container(old_file_path, new_file_path, ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error renaming file: {err}")

    # Track the rename operation - handle chained renames (A→B→C should store A→C)
    existing_rename = next(
        (rf for rf in ctx.deps.renamed_files if rf.new_path == str(old_file_path)),
        None
    )

    if existing_rename:
        # Update the existing rename to point to the new final path
        existing_rename.new_path = str(new_file_path)
    else:
        # First rename for this file
        ctx.deps.renamed_files.append(RenamedFile(
            old_path=str(old_file_path),
            new_path=str(new_file_path),
            content=content
        ))

    # Update tracked files if the renamed file was in new_files or modified_files
    for i, f in enumerate(ctx.deps.new_files):
        if f.path == str(old_file_path):
            ctx.deps.new_files[i] = FileInRun(
                path=str(new_file_path), content=f.content)

    for i, f in enumerate(ctx.deps.modified_files):
        if f.path == str(old_file_path):
            ctx.deps.modified_files[i] = FileInRun(
                path=str(new_file_path),
                content=f.content,
                old_content=f.old_content
            )

    return f"Successfully renamed {old_path} to {new_path}"


async def delete_file(ctx: RunContext[SWEAgentDeps], file_path: str) -> str:
    """
    Delete a file from the project.
    This permanently removes the file. Use with caution.

    Args:
        ctx: The context.
        file_path: The path of the file to delete.

    Returns:
        str: Confirmation message.
    """
    path = Path(file_path)

    if not await check_file_exists_in_container(path, ctx.deps.container_name):
        raise ModelRetry(f"File {file_path} does not exist.")

    # Read the content before deleting for revert purposes
    # Only store full content for text-based files with allowed extensions
    file_content = await read_file_from_container(path, ctx.deps.container_name)
    content = filter_content_by_extension(path, file_content)

    _, err = await remove_from_container(path, ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error deleting file: {err}")

    # Track the deletion
    ctx.deps.deleted_files.append(FileInRun(path=str(path), content=content))

    # Remove from new_files or modified_files if it was there
    ctx.deps.new_files = [f for f in ctx.deps.new_files if f.path != str(path)]
    ctx.deps.modified_files = [
        f for f in ctx.deps.modified_files if f.path != str(path)]

    return f"Successfully deleted {file_path}"


file_editing_toolset = FunctionToolset(
    tools=[
        write_file,
        replace_file_lines,
        add_file_lines,
        delete_file_lines,
        rename_file,
        delete_file
    ],
    max_retries=3
)
