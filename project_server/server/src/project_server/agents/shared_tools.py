from typing import Literal, Optional
from pydantic_ai import ModelRetry, RunContext, FunctionToolset

from project_server.utils.code_utils import add_line_numbers_to_script, run_python_code_in_container, run_shell_code_in_container, is_readable_extension
from synesis_schemas.main_server import GetGuidelinesRequest
from project_server.client.requests.knowledge_bank import get_task_guidelines
from project_server.app_secrets import READABLE_EXTENSIONS


async def execute_python_code(ctx: RunContext, python_code: str):
    """
    Execute a python code block.

    Args:
        python_code: The python code to execute.
        explanation: Explanation of what you are doing and why - very concisely.
    """

    assert hasattr(ctx.deps, "container_name"), "Container name is required"

    out, err = await run_python_code_in_container(python_code, container_name=ctx.deps.container_name)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out


async def get_task_guidelines_tool(ctx: RunContext, task: Literal["time_series_forecasting"]) -> str:
    assert hasattr(ctx.deps, "client"), "Client is required"
    return await get_task_guidelines(ctx.deps.client, GetGuidelinesRequest(task=task))


async def grep_tool(ctx: RunContext, pattern: str, path: str = "/app", recursive: bool = True) -> str:
    """
    Search for a pattern in files using grep.

    Args:
        ctx: The run context.
        pattern: The pattern to search for (regex pattern).
        path: The directory or file path to search in (default: /app).
        recursive: Whether to search recursively (default: True).

    Returns:
        Matching lines with file paths and line numbers.
    """
    # Code files where we show all matches
    CODE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx',
                       '.sh', '.bash', '.zsh', '.sql', '.html', '.css'}
    MAX_LINES_PER_FILE = 10

    cmd = f"grep -rn"
    if not recursive:
        cmd = f"grep -n"

    shell_code = f"{cmd} '{pattern}' {path} || true"

    out, err = await run_shell_code_in_container(
        shell_code,
        container_name=ctx.deps.container_name
    )

    if err:
        raise ModelRetry(f"Error running grep: {err}")

    if not out.strip():
        return f"No matches found for pattern '{pattern}' in {path}"

    # Truncate data/config files and non-readable files to prevent token overflow
    filtered_lines = []
    file_match_counts = {}

    for line in out.split('\n'):
        if ':' in line:
            # Parse grep output format: file_path:line_number:content
            parts = line.split(':', 2)
            if len(parts) >= 3:
                file_path = parts[0]

                # Check if this is a code file (show all) or needs truncation
                is_code_file = any(file_path.lower().endswith(ext)
                                   for ext in CODE_EXTENSIONS)

                # Truncate everything except code files (includes .json, .xml, .yaml, .log, .csv, etc.)
                if not is_code_file:
                    if file_path not in file_match_counts:
                        file_match_counts[file_path] = 0
                    file_match_counts[file_path] += 1

                    if file_match_counts[file_path] <= MAX_LINES_PER_FILE:
                        filtered_lines.append(line)
                    elif file_match_counts[file_path] == MAX_LINES_PER_FILE + 1:
                        filtered_lines.append(
                            f"{file_path}:...:... ({file_match_counts[file_path] - MAX_LINES_PER_FILE} more matches truncated)")
                    continue

        filtered_lines.append(line)

    # Add summary for truncated files
    truncated_files = {f: count for f, count in file_match_counts.items()
                       if count > MAX_LINES_PER_FILE}
    if truncated_files:
        filtered_lines.append("\n--- Truncation Summary ---")
        for file_path, total_matches in truncated_files.items():
            filtered_lines.append(
                f"{file_path}: {total_matches} total matches (showing first {MAX_LINES_PER_FILE})")

    return '\n'.join(filtered_lines)


async def ls_tool(ctx: RunContext, path: str = "/app", show_hidden: bool = False, long_format: bool = False) -> str:
    """
    List directory contents.

    Args:
        ctx: The run context.
        path: The directory path to list (default: /app).
        show_hidden: Whether to show hidden files (default: False).
        long_format: Whether to show detailed information (default: False).

    Returns:
        Directory listing.
    """
    assert hasattr(ctx.deps, "container_name"), "Container name is required"
    cmd = "ls"
    if long_format:
        cmd += " -l"
    if show_hidden:
        cmd += " -a"

    shell_code = f"{cmd} {path} || true"

    out, err = await run_shell_code_in_container(
        shell_code,
        container_name=ctx.deps.container_name,
    )

    if err:
        raise ModelRetry(f"Error running ls: {err}")

    if not out.strip():
        return f"Directory {path} is empty or does not exist"

    return out


async def read_file_tool(ctx: RunContext, file_path: str) -> str:
    """
    Read the contents of a text-based file.
    Only supports common text file formats: .py, .txt, .md, .json, .yaml, .yml, .toml, .ini, .cfg, .conf, .sh, .bash, .zsh, .csv, .xml, .html, .css, .js, .ts, .jsx, .tsx, .sql, .log

    Args:
        ctx: The run context.
        file_path: The path to the file to read (relative to /app or absolute).

    Returns:
        The file contents.
    """
    assert hasattr(ctx.deps, "container_name"), "Container name is required"

    # Check if file has an allowed extension
    if not is_readable_extension(file_path):
        raise ModelRetry(
            f"File {file_path} does not have an allowed extension. Only text-based files are supported: {', '.join(sorted(READABLE_EXTENSIONS))}")

    shell_code = f"cat {file_path} || echo 'Error: File not found or cannot be read'"

    out, err = await run_shell_code_in_container(
        shell_code,
        container_name=ctx.deps.container_name,
    )

    if err:
        raise ModelRetry(f"Error reading file: {err}")

    if "Error:" in out or not out.strip():
        raise ModelRetry(f"Could not read file {file_path}: {out.strip()}")

    out_with_line_numbers = add_line_numbers_to_script(out)

    return f"READ FILE: {file_path}\n\n<begin_file file_path={file_path}>\n\n{out_with_line_numbers}\n\n<end_file>"


async def find_tool(ctx: RunContext, name_pattern: str, path: str = "/app", file_type: Optional[str] = None) -> str:
    """
    Find files or directories by name pattern.

    Args:
        ctx: The run context.
        name_pattern: The pattern to match (e.g., "*.py", "config.json", "myfile").
        path: The directory to search in (default: /app).
        file_type: Optional filter: "f" for files only, "d" for directories only (default: None for both).

    Returns:
        List of matching file/directory paths.
    """
    assert hasattr(ctx.deps, "container_name"), "Container name is required"
    cmd = "find"
    if file_type:
        cmd += f" -type {file_type}"

    shell_code = f"{cmd} {path} -name '{name_pattern}' 2>/dev/null || true"

    out, err = await run_shell_code_in_container(
        shell_code,
        container_name=ctx.deps.container_name,
    )

    if err:
        raise ModelRetry(f"Error running find: {err}")

    if not out.strip():
        return f"No files or directories found matching pattern '{name_pattern}' in {path}"

    return out


navigation_toolset = FunctionToolset(
    tools=[
        # Grep doesnt work so well, keeps reading large data files, todo fix
        # grep_tool,
        read_file_tool,
        ls_tool,
        find_tool
    ],
    max_retries=3
)
