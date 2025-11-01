import re
import asyncio
from typing import Tuple, Optional

from project_server.worker import logger


def parse_code(python_code: str) -> str:
    matches = re.findall(r'```(?:\w+\n)?(.*?)```', python_code, re.DOTALL)
    if matches:
        return "\n\n".join(matches).strip()

    return python_code.strip()


async def run_python_code_in_container(
        python_code: str,
        container_name: str,
        cwd: str | None = None) -> Tuple[str, str]:
    """
    Helper function that runs Python code inside a Docker container.
    This is an async version that uses asyncio.create_subprocess_exec for non-blocking execution.
    """
    python_code_parsed = parse_code(python_code)

    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"{f'cd {cwd} &&' if cwd else ''} python -c 'import sys; exec(sys.stdin.read())'"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate(python_code_parsed.encode('utf-8'))
    err_str = err.decode("utf-8") if process.returncode != 0 else ""

    return out.decode("utf-8"), err_str


async def run_python_function_in_container(
        base_script: str,
        function_name: str,
        input_variables: list[str],
        container_name: str,
        source_module: Optional[str] = None,
        print_output: bool = False,
        async_function: bool = False
) -> Tuple[str, str]:
    """
    Run a Python function in the container. 
    Wrote this function to avoid writing raw code inside strings all over.
    """

    raw_code = f"from {source_module} import {function_name}\n\n" if source_module else ""
    raw_code += f"import asyncio\n\n" if async_function else ""
    raw_code += f"{base_script}\n\n"
    if async_function:
        raw_code += (
            "async def run_function():\n" +
            f"    output = await {function_name}({', '.join(input_variables)})\n" +
            (f"    print(output)\n" if print_output else "") +
            "\nasyncio.run(run_function())"
        )
    else:
        raw_code += (
            f"output = {function_name}({', '.join(input_variables)})\n" +
            "print(output)" if print_output else ""
        )

    out, err = await run_python_code_in_container(raw_code, container_name)

    logger.info(f"Raw code:\n\n{raw_code}")
    logger.info(f"Out:\n\n{out}")
    logger.info(f"Err:\n\n{err}")

    return out, err


async def run_shell_code_in_container(
        shell_code: str,
        container_name: str,
        cwd: str | None = None) -> Tuple[str, str]:
    """
    Helper function that actually runs Shell code inside a Docker container.
    This is an async version that uses asyncio.create_subprocess_exec for non-blocking execution.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"{f'cd {cwd} &&' if cwd else ''} set -e; set -o pipefail;\n{shell_code}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    err = None if process.returncode == 0 else err.decode("utf-8")

    return out.decode("utf-8"), err


def add_line_numbers_to_script(script: str) -> str:
    """
    Add right-aligned line numbers to a script.
    """
    script = script.strip()
    lines = [line for line in script.splitlines()]
    max_width = len(str(len(lines)))
    return "\n".join(f"{str(i+1).rjust(max_width)}. {line}" for i, line in enumerate(lines))


def remove_line_numbers_from_script(script: str) -> str:
    """
    Remove line numbers from a script.
    """
    lines = [line for line in script.splitlines()]
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(re.sub(r'^\d+\.\s?', '', line.strip()))

    return "\n".join(cleaned_lines)


def replace_lines_in_script(
        script: str,
        line_number_start: int,
        line_number_end: int,
        new_code: str,
        script_has_line_numbers: bool = False
) -> str:
    """
    Replace lines in a script.

    Args:
        script: The script to modify
        line_number_start: The starting line number (1-indexed, inclusive)
        line_number_end: The ending line number (1-indexed, inclusive)
        new_code: The new code to insert
        script_has_line_numbers: Whether the script has line numbers

    Returns:
        str: The modified script
    """

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    lines = [line for line in script.splitlines()]
    new_lines = [line for line in new_code.splitlines()]

    lines[line_number_start-1:line_number_end] = new_lines
    updated_script = "\n".join(lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def add_lines_to_script_at_line(
        script: str,
        new_code: str,
        start_line: int,
        script_has_line_numbers: bool = False) -> str:

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    script_lines = [line for line in script.splitlines()]
    lines_to_add = [line for line in new_code.splitlines()]
    # Convert 1-indexed to 0-indexed with bounds checking
    # Allow appending beyond the end of file
    start_line_idx = max(0, min(start_line - 1, len(script_lines)))

    updated_lines = script_lines[:start_line_idx] + \
        lines_to_add + script_lines[start_line_idx:]
    updated_script = "\n".join(updated_lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def delete_lines_from_script(
        script: str,
        line_number_start: int,
        line_number_end: int,
        script_has_line_numbers: bool = False) -> str:

    if script_has_line_numbers:
        script = remove_line_numbers_from_script(script)

    script = script.strip()
    lines = [line for line in script.splitlines()]
    # Convert 1-indexed to 0-indexed with bounds checking
    line_number_start_idx = max(0, min(line_number_start - 1, len(lines) - 1))
    line_number_end_idx = max(line_number_start_idx, min(
        line_number_end - 1, len(lines) - 1))

    updated_lines = lines[:line_number_start_idx] + \
        lines[line_number_end_idx + 1:]
    updated_script = "\n".join(updated_lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def remove_print_statements_from_code(code: str) -> str:
    pattern = r'print\s*\([^)]*\)'
    cleaned_code = re.sub(pattern, '', code)
    lines = cleaned_code.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]

    return '\n'.join(cleaned_lines)
