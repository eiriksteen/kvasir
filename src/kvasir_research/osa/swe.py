from uuid import UUID
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models import ModelSettings

from kvasir_research.worker import logger
from kvasir_research.utils.agent_utils import get_model
from kvasir_research.history_processors import keep_only_most_recent_script
from kvasir_research.utils.docker_utils import (
    check_file_exists_in_container,
    write_file_to_container,
    read_file_from_container,
    remove_from_container,
    is_subpath
)
from kvasir_research.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
    run_python_code_in_container,
    run_shell_code_in_container
)
from kvasir_research.utils.agent_utils import get_working_directory_description, get_folder_structure_description, get_injected_analyses
from kvasir_research.osa.shared_tools import read_files_tool


SWE_SYSTEM_PROMPT = f"""
You are a professional software engineer, specialized in data science and ML engineering.  
You are tasked with writing data science and ML engineering code based on a task description. 

Typical problems include:
- Data cleaning and preparation
- Feature engineering
- Experiment (model building, training, and evaluation)
- Model deployment

You will work within a Python package. 
You may be provided some past analyses you can use to inform your work. 
Pay close attention to the deliverable description. 

Create / modify relevant modules and create a main Python or Bash script that will be executed to produce the output (must be directly runnable, no syntax errors). 
Often you will create an output you save to a file. The orchestrator may want you to print relevant quantities as well to avoid reading files. 
We separate modules and scripts in our projects: create only classes, functions, and reusable code inside src/. Executable scripts should be placed outside src/ (e.g., in scripts/ or another appropriate location based on the project structure).
When submitting results, provide an execution_command that will be executed via shell to run your main script with any necessary configuration parameters. 
Unless otherwise specified, put all results for a run in a results/[method_name]/[some_run_id_you_compute_or_choose] directory. 
Your code must fit into the overall module! No general names like "execution_command.sh", be specific and organised, maintain a nice folder structure. 

Organize inputs and outputs as Python dataclasses with clear, descriptive field names.
Use concise but covering docstrings for all functions and classes, including descriptions of inputs, outputs, and behavior. 
Use type hints consistently throughout the code for all function parameters, return values, and class attributes. 
Choose names that clearly convey purpose and intent. 
The specific fields and structure will depend on the user prompt, and if no instruction is given, you must decide based on the task requirements. 

Device selection should be cuda if available, then mps if available, then cpu.
"""


@dataclass
class SWEDeps:
    run_id: str
    container_name: str
    orchestrator_id: UUID
    project_path: Path
    project_id: UUID
    data_paths: List[str]
    injected_analyses: List[str]
    read_only_paths: List[str]
    modified_files: Dict[str, str] = field(default_factory=dict)


model = get_model()


swe_agent = Agent[SWEDeps, str](
    model,
    deps_type=SWEDeps,
    tools=[read_files_tool],
    retries=3,
    history_processors=[keep_only_most_recent_script],
    model_settings=ModelSettings(temperature=0)
)


@swe_agent.system_prompt
async def swe_system_prompt(ctx: RunContext[SWEDeps]) -> str:
    current_wd = await get_working_directory_description(ctx.deps.container_name)
    folder_structure = await get_folder_structure_description(ctx.deps.container_name)
    analyses_str = await get_injected_analyses(ctx.deps.injected_analyses)

    full_system_prompt = (
        f"{SWE_SYSTEM_PROMPT}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Folder structure: {folder_structure}\n\n" +
        f"Data paths to use: {ctx.deps.data_paths}\n\n" +
        f"Read only paths: {ctx.deps.read_only_paths}\n\n" +
        f"Here are results from previous analyses:\n\n<analyses>\n{analyses_str}\n</analyses>"
    )

    return full_system_prompt


@swe_agent.tool
async def write_script(ctx: RunContext[SWEDeps], content: str, file_path: str) -> str:
    """
    Write a new script to a file. 
    This is only for creating new scripts. To modify existing scripts, use add_script_lines, replace_script_lines, or delete_script_lines instead.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        content: The content to write to the file.
        file_path: The path to the file to write the content to (including the file name). Will be run from the cwd. Accepts absolute or relative paths. 

    Returns:
        str: The script with line numbers.
    """
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] write_script called: file_path={file_path}, content_length={len(content)} chars")

    file_path = Path(file_path)
    if not _validate_path_permissions(file_path, ctx.deps.read_only_paths):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if await check_file_exists_in_container(file_path, ctx.deps.container_name):
        raise ModelRetry(
            f"File {file_path} already exists. To modify an existing file, use add_script_lines, replace_script_lines, or delete_script_lines instead. write_script is only for creating new files.")

    await write_file_to_container(
        file_path,
        content,
        ctx.deps.container_name
    )

    # Track the modified file
    ctx.deps.modified_files[str(file_path)] = content

    content_with_line_numbers = add_line_numbers_to_script(content)

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] write_script completed: file_path={file_path}")

    return f"WROTE TO FILE: {file_path}\n\n<begin_file file_path={file_path}>\n\n{content_with_line_numbers}\n\n<end_file>"


@swe_agent.tool
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
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] replace_script_lines called: file_path={file_path}, lines={line_number_start}-{line_number_end}, new_code_length={len(new_code)} chars")

    file_path = Path(file_path)
    if not _validate_path_permissions(file_path, ctx.deps.read_only_paths):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

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

    # Track the modified file
    ctx.deps.modified_files[str(file_path)] = updated_content

    updated_content_with_line_numbers = add_line_numbers_to_script(
        updated_content)
    out = f"UPDATED FILE: {file_path}\n\n <begin_file file_path={file_path}>\n\n {updated_content_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe file is not automatically run and validated, you must call the final_result tool to submit the file for validation and feedback.\n"

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] replace_script_lines completed: file_path={file_path}")

    return out


@swe_agent.tool
async def add_script_lines(ctx: RunContext[SWEDeps], file_name: str, new_code: str, start_line: int) -> str:
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
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] add_script_lines called: file_name={file_name}, start_line={start_line}, new_code_length={len(new_code)} chars")

    file_path = Path(file_name)
    if not _validate_path_permissions(file_path, ctx.deps.read_only_paths):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

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

    # Track the modified file
    ctx.deps.modified_files[str(file_path)] = updated_content

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <begin_file file_path={file_path}>\n\n {script_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] add_script_lines completed: file_path={file_path}")

    return out


@swe_agent.tool
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
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] delete_script_lines called: file_path={file_path}, lines={line_number_start}-{line_number_end}")

    file_path = Path(file_path)

    if not _validate_path_permissions(file_path, ctx.deps.read_only_paths):
        raise ModelRetry(
            f"File {file_path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

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

    # Track the modified file
    ctx.deps.modified_files[str(file_path)] = updated_content

    script_with_line_numbers = add_line_numbers_to_script(updated_content)
    out = f"UPDATED SCRIPT: \n\n <begin_file file_path={file_path}>\n\n {script_with_line_numbers}\n\n <end_file>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] delete_script_lines completed: file_path={file_path}")

    return out


@swe_agent.tool
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
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] delete_file called: file_path={file_path}")

    path = Path(file_path)
    if not _validate_path_permissions(path, ctx.deps.read_only_paths):
        raise ModelRetry(
            f"File {path} is not writable. It is in a read-only path. Read-only paths: {', '.join(ctx.deps.read_only_paths)}")

    if not await check_file_exists_in_container(path, ctx.deps.container_name):
        raise ModelRetry(f"File {file_path} does not exist.")

    _, err = await remove_from_container(path, ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error deleting file: {err}")

    # Remove from modified_files tracking if it was there
    if str(file_path) in ctx.deps.modified_files:
        del ctx.deps.modified_files[str(file_path)]

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] delete_file completed: file_path={file_path}")

    return f"Successfully deleted {file_path}"


@swe_agent.output_validator
async def submit_results(ctx: RunContext[SWEDeps], execution_command: str) -> str:
    """
    Submit the execution command that runs your main script (which you should have created outside src/) and produces the output. 
    The execution_command should be a shell command (e.g., "python scripts/train_model.py --epochs 100" or "bash run_pipeline.sh").
    Remember to use any relevant evaluation code, if specified. 
    """
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] submit_results called: execution_command={execution_command}")

    # If no execution command provided (e.g., only module modifications), skip execution
    if not execution_command or execution_command.strip() == "":
        result = _modified_files_to_string(
            ctx.deps.modified_files, ctx.deps.run_id, "", "")
        logger.info(
            f"SWE Agent [{ctx.deps.run_id}] submit_results completed (no execution): modified_files={list(ctx.deps.modified_files.keys())}")
        return result

    # Execute the command via shell
    out, err = await run_shell_code_in_container(execution_command, ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error running command '{execution_command}': {err}")

    result = _modified_files_to_string(
        ctx.deps.modified_files, ctx.deps.run_id, execution_command, out)

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] submit_results completed: output_length={len(out)} chars, modified_files={list(ctx.deps.modified_files.keys())}")

    return result

##


def _modified_files_to_string(modified_files: Dict[str, str], run_id: str, execution_command: str, execution_output: str) -> str:
    result = [f'<swe_result run_id="{run_id}">']

    if not modified_files:
        result.append("")
        result.append("  (no files modified)")
    else:
        for file_path, content in modified_files.items():
            result.append("")
            result.append(f'  <file path="{file_path}">')
            # Indent content lines
            for line in content.split("\n"):
                result.append(f"    {line}")
            result.append("  </file>")

    # Add execution command if provided
    if execution_command:
        result.append("")
        result.append(
            f'  <execution_command>{execution_command}</execution_command>')

    # Add execution output
    if execution_output:
        result.append("")
        result.append("  <execution_output>")
        for line in execution_output.split("\n"):
            result.append(f"    {line}")
        result.append("  </execution_output>")

    result.append("")
    result.append("</swe_result>")

    return "\n".join(result)


def _validate_path_permissions(path: str | Path, read_only_paths: List[str | Path]) -> bool:
    path = Path(path).resolve()

    # Check if path is in any read-only path
    for read_only_path in read_only_paths:
        if is_subpath(path, Path(read_only_path).resolve()):
            return False

    return True
