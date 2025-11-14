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
    run_shell_code_in_container_streaming
)
from kvasir_research.utils.file_utils import get_working_directory_description, get_folder_structure_description
from kvasir_research.utils.agent_utils import get_injected_analyses, get_dockerfile_for_env_description
from kvasir_research.osa.shared_tools import read_files_tool, ls_tool


# Static guidelines, later we can adapt this based on user codebases
CODING_GUIDELINES = """
## Coding Guidelines

### 1. Project Structure
We maintain an organized data science codebase with clear separation of concerns:

```
├── data/              # Raw and processed datasets
├── analysis/          # Exploratory notebooks and ad-hoc analysis
├── scripts/           # Executable entry points
├── runs/              # All experiment runs and outputs
└── src/               # Reusable modules and packages
    └── <package_name>/
        ├── models/
        ├── data_processing/
        ├── evaluation/
        ├── utils/
        └── __init__.py
```

### 2. File Organization

**Module vs Script Separation:**
- `src/`: Only reusable code (classes, functions, utilities)
- `scripts/`: Executable entry points that import from src/
- Keep src/ free of executable scripts

**Deliverables:**
- Create a main Python or Bash script that produces the required output
- Script must be directly runnable with no syntax errors
- Output an execution_command (shell command) to run your script

### 3. Run Management

**All run artifacts must be contained in runs/ directories:**
- Path structure: `runs/[method_name]/[run_id]/`
- Use readable, descriptive run IDs (enumerate if needed)
- Include the configuration yaml file in each run directory
- NO config files or results outside of runs/ folders! Delete them if you mistakenly put them there. 

**Output Guidelines:**
- Save outputs to files within the run directory
- Print key metrics to stdout by default (for orchestrator visibility)
- The orchestrator should not need to read files for critical metrics
- Save plots and visualizations to the run directory!

### 4. Configuration

**All scripts must accept configuration via YAML:**
- Script should take yaml path as a command-line argument
- Example: `python scripts/train_model.py --config runs/experiment_01/config.yaml`
- Store the config file alongside run results

### 5. Code Quality

**Naming Conventions:**
- Be specific and descriptive (avoid generic names like `process_data`, `run_model`)
- Use clear, intent-revealing names for files, functions, and variables
- Example: `train_transformer_model.py` not `model.py`

**Type Safety & Documentation:**
- Use Python dataclasses for structured inputs/outputs
- Apply type hints to all function parameters, returns, and class attributes
- Write concise docstrings covering inputs, outputs, and behavior

**Device Selection:**
- Priority: CUDA (if available) → MPS (if available) → CPU

**Progress Tracking:**
- Use TQDM, and print metrics and other logging quantities to the terminal during the run

### 6. Integration

- Ensure your code integrates with the overall project structure
- Use specific, organized naming (no generic names like `execution_command.sh`)
- Maintain a clean folder hierarchy
- When in doubt about structure, follow the established pattern
"""


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
You are working within a package, and we have done pip install -e ., so import from the package (do not use src, use the package name directly)
NB: The final execution command output must be directly runnable in bash. No syntax errors. Do not write "execution_command: " then your command, just write the command

{CODING_GUIDELINES}

Use insights from any provided analyses to inform your work! It must be based on strong data understanding!

## Communicating with the Orchestrator

If you need help from the orchestrator, use `submit_message_to_orchestrator`. This pauses your run and sends a message to the orchestrator, which will respond and resume your run with the answer. Use this when you need to:
- Request an analysis to answer questions about the data (e.g., "Please analyze the distribution of missing values in column X")
- Request access to write to a read-only path if absolutely necessary
- Report critical issues that require orchestrator intervention
- Ask for clarification on ambiguous requirements

The orchestrator will handle your request (e.g., launch an analysis agent) and resume your run with a response. Be specific about what you need.
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
    time_limit: int  # Time limit in seconds
    modified_files: Dict[str, str] = field(default_factory=dict)


async def submit_implementation_results(ctx: RunContext[SWEDeps], execution_command: str) -> str:
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

    # Execute the command via shell with streaming and timeout
    stdout_lines = []
    stderr_lines = []
    return_code = None
    timeout_message = None

    async for stream_type, content in run_shell_code_in_container_streaming(
        execution_command,
        ctx.deps.container_name,
        timeout=ctx.deps.time_limit
    ):
        if stream_type == "returncode":
            return_code = content
        elif stream_type == "stdout":
            stdout_lines.append(content)
            logger.info(f"[{ctx.deps.run_id}] stdout: {content}")
        elif stream_type == "stderr":
            stderr_lines.append(content)
            logger.info(f"[{ctx.deps.run_id}] stderr: {content}")
        elif stream_type == "timeout":
            timeout_message = content
            logger.warning(f"[{ctx.deps.run_id}] Timeout: {content}")

    # Handle timeout
    if timeout_message:
        partial_out = "\n".join(stdout_lines)
        if partial_out:
            partial_out += "\n\n"

        error_msg = (
            f"{partial_out}"
            f"ERROR: Time limit exceeded ({ctx.deps.time_limit}s)\n"
            f"The execution was terminated because it exceeded the allocated time limit.\n"
            f"Consider optimizing the code, reducing the problem size, or using more efficient algorithms."
        )
        result = _modified_files_to_string(
            ctx.deps.modified_files, ctx.deps.run_id, execution_command, error_msg)
        logger.info(
            f"SWE Agent [{ctx.deps.run_id}] submit_results time limit exceeded: {ctx.deps.time_limit}s")
        return result

    # Combine output
    out = "\n".join(stdout_lines)
    err = "\n".join(stderr_lines) if return_code != 0 else None

    if err:
        logger.info(
            f"SWE Agent [{ctx.deps.run_id}] submit_results error: execution_command={execution_command}, error={err}")
        raise ModelRetry(f"Error running command '{execution_command}': {err}")

    result = _modified_files_to_string(
        ctx.deps.modified_files, ctx.deps.run_id, execution_command, out)

    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] submit_results completed: output_length={len(out)} chars, modified_files={list(ctx.deps.modified_files.keys())}")

    return result


async def submit_message_to_orchestrator(ctx: RunContext[SWEDeps], message: str) -> str:
    """
    Submit a message to the orchestrator for help, to request an analysis, request access to write a file, or notify it of any critical issues. 
    """
    logger.info(
        f"SWE Agent [{ctx.deps.run_id}] submit_message_to_orchestrator called: message={message}")
    result = _modified_files_to_string(
        ctx.deps.modified_files, ctx.deps.run_id, "", message)
    return result


model = get_model()


swe_agent = Agent[SWEDeps, str](
    model,
    deps_type=SWEDeps,
    tools=[read_files_tool, ls_tool],
    output_type=[
        submit_implementation_results,
        submit_message_to_orchestrator
    ],
    retries=5,
    history_processors=[keep_only_most_recent_script],
    model_settings=ModelSettings(temperature=0)
)


@swe_agent.system_prompt
async def swe_system_prompt(ctx: RunContext[SWEDeps]) -> str:
    current_wd = await get_working_directory_description(ctx.deps.container_name)
    folder_structure = await get_folder_structure_description(ctx.deps.container_name)
    analyses_str = await get_injected_analyses(ctx.deps.injected_analyses)
    dockerfile_str = get_dockerfile_for_env_description()

    full_system_prompt = (
        f"{SWE_SYSTEM_PROMPT}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Folder structure: {folder_structure}\n\n" +
        f"Data paths to use: {ctx.deps.data_paths}\n\n" +
        f"Read only paths: {ctx.deps.read_only_paths}\n\n" +
        f"You environment is described by the following Dockerfile:\n\n<dockerfile>\n{dockerfile_str}\n</dockerfile>\n\n" +
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
