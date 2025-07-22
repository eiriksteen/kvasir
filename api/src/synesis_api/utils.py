import re
import json
import tempfile
import markdown2
import sys
import asyncio
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from pylint import lint
from io import StringIO
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from synesis_api.secrets import (
    OPENAI_API_KEY,
    OPENAI_API_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_API_MODEL,
    MODEL_TO_USE,
    GOOGLE_API_KEY,
    GOOGLE_API_MODEL
)
from datetime import datetime


def get_model():

    if MODEL_TO_USE == "anthropic":
        provider = AnthropicProvider(api_key=ANTHROPIC_API_KEY)
        model = AnthropicModel(
            model_name=ANTHROPIC_API_MODEL,
            provider=provider
        )
    elif MODEL_TO_USE == "google":
        provider = GoogleProvider(api_key=GOOGLE_API_KEY)
        model = GoogleModel(model_name=GOOGLE_API_MODEL, provider=provider)
    else:
        provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=provider
        )

    return model


def save_markdown_as_html(markdown_content: str):
    # Convert markdown to HTML
    html_content = markdown2.markdown(markdown_content, extras=[
                                      "tables", "fenced-code-blocks"])

    # Wrap it in a basic HTML structure to improve styling
    full_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3, h4, h5, h6 {{ color: #333; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
            code {{ font-family: monospace; color: #d63384; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Save the HTML to a file
    return full_html


def parse_code(python_code: str) -> str:
    matches = re.findall(r'```(?:\w+\n)?(.*?)```', python_code, re.DOTALL)
    if matches:
        return "\n\n".join(matches).strip()

    return python_code.strip()


async def run_python_code_in_container(
        python_code: str,
        container_name: str = "synesis-sandbox",
        cwd: str | None = None) -> Tuple[str, str]:
    """
    Helper function that runs Python code inside a Docker container named `sandbox` (by default).
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

    return out.decode("utf-8"), err.decode("utf-8")


async def run_python_function_in_container(
        base_script: str,
        function_name: str,
        input_variables: list[str],
        container_name: str = "synesis-sandbox",
        source_module: Optional[str] = None,
        print_output: bool = False,
        async_function: bool = False
):
    """
    Run a Python function in the container. 
    Wrote this function to avoid writing raw code inside strings all over.
    """

    raw_code = (
        f"from {source_module} import {function_name}\n\n" if source_module else ""
        f"{base_script}\n\n"
        f"output = {'await' if async_function else ''} {function_name}({', '.join(input_variables)})"
        f"print(output)" if print_output else ""
    )

    out, err = await run_python_code_in_container(raw_code, container_name)

    return out, err


async def run_shell_code_in_container(
        shell_code: str,
        container_name: str = "synesis-sandbox",
        cwd: str | None = None) -> Tuple[str, str]:
    """
    Helper function that actually runs Shell code inside a Docker container named `sandbox` (by default).
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


async def copy_file_or_directory_to_container(
        path: Path,
        target_dir: str = "/tmp",
        container_name: str = "synesis-sandbox"):
    """
    Copy a file or directory to the container.
    """
    cmd = [
        "docker", "cp", path, f"{container_name}:{target_dir}/{path.name}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


async def copy_file_from_container(
        file_path: Path,
        target_dir: str = "/tmp",
        container_name: str = "synesis-sandbox"):
    """
    Copy a file or directory from the container.
    """
    cmd = [
        "docker", "cp", f"{container_name}:{file_path}", target_dir
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


async def create_file_in_container_with_content(
        file_path: Path,
        content: str,
        container_name: str = "synesis-sandbox"):
    """
    Create a file in the container with the given content.
    Ensures the directory exists and creates the file before writing.
    """
    escaped_content = content.replace("'", "'\\''")

    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"mkdir -p $(dirname {file_path}) && touch {file_path} && echo '{escaped_content}' > {file_path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


async def remove_from_container(
        directory_path: Path,
        container_name: str = "synesis-sandbox"):
    """
    Remove a file or directory from the container.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "rm", "-rf", f"{directory_path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


def get_basic_df_info(df: pd.DataFrame):
    shape = df.shape
    sample_data = df.head()
    info = df.info()
    description = df.describe()

    return f"Shape: {shape}\nSample Data: {sample_data}\nInfo: {info}\nDescription: {description}"


def get_df_info(df: pd.DataFrame, max_cols: int = 10):
    """
    Returns a string containing basic information about the DataFrame, including the shape, sample data, info, description, and correlation matrix.

    Returns:
        str: A formatted string containing the DataFrame information
    """
    # Initialize list to store output strings
    output = []

    # Base info functions that are always shown
    info_functions = {
        "DATA SHAPE": lambda df: df.shape,
        "SAMPLE DATA": lambda df: df.head(),
        "DATA INFO": lambda df: df.info(),
        "DATA DESCRIPTION": lambda df: df.describe(),
        "DATA CORRELATION": lambda df: df.select_dtypes(include=['int', 'float', 'bool'])[
            df.select_dtypes(
                include=['int', 'float', 'bool']).columns[:max_cols]
        ].corr()
    }

    # Get categorical columns (including potential integer categories)
    categorical_cols = (
        df.select_dtypes(include=['object', 'category']).columns.tolist() +
        [col for col in df.select_dtypes(include=['int', 'int64']).columns
         # columns with less than 5% unique values
         if df[col].nunique() < len(df) * 0.05]
    )

    if len(df.columns) <= max_cols:
        # For smaller datasets, show detailed null percentages and categorical unique counts
        info_functions.update({
            "DATA NULL PERCENTAGES": lambda df: (df.isnull().sum() / len(df)).sort_values(ascending=False),
            "CATEGORICAL UNIQUE VALUES": lambda df: df[categorical_cols].nunique() if len(categorical_cols) > 0 else "No categorical columns found"
        })
    else:
        # For larger datasets, show summary statistics
        def null_stats(df): return pd.Series({
            'min null percentage': (df.isnull().sum() / len(df)).min(),
            'max null percentage': (df.isnull().sum() / len(df)).max(),
            'mean null percentage': (df.isnull().sum() / len(df)).mean()
        })

        def unique_cat_stats(df): return pd.Series({
            'min unique values': df[categorical_cols].nunique().min() if len(categorical_cols) > 0 else "No categorical columns",
            'max unique values': df[categorical_cols].nunique().max() if len(categorical_cols) > 0 else "No categorical columns",
            'mean unique values': df[categorical_cols].nunique().mean() if len(categorical_cols) > 0 else "No categorical columns"
        })

        info_functions.update({
            "NULL VALUE STATISTICS": null_stats,
            "CATEGORICAL UNIQUE VALUE STATISTICS": unique_cat_stats
        })

    for section, func in info_functions.items():
        try:
            output.append(f"[{section}]\n")
            output.append(str(func(df)))
            output.append("\n")  # Add extra newline between sections
        except Exception as e:
            output.append(f"Failed to get {section.lower()}: {e}\n")

    return "".join(output)


def extract_json_from_markdown(string: str) -> dict:

    pattern = r'```json\s*(.*?)\s*```'

    matches = re.finditer(pattern, string, re.DOTALL)

    matches_list = list(matches)

    if not matches_list:
        raise ValueError("No JSON code blocks found in the string")

    last_json_content = matches_list[-1].group(1).strip()

    return json.loads(last_json_content)


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
        line_number_start: The starting line number (0-indexed)
        line_number_end: The ending line number (0-indexed, inclusive)
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
    start_line = max(0, min(start_line, len(script_lines))-1)

    updated_lines = script_lines[:start_line] + \
        lines_to_add + script_lines[start_line:]
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
    line_number_start = max(0, min(line_number_start, len(lines))-1)
    line_number_end = max(line_number_start, min(
        line_number_end, len(lines) - 1))

    updated_lines = lines[:line_number_start] + lines[line_number_end + 1:]
    updated_script = "\n".join(updated_lines)

    if script_has_line_numbers:
        updated_script = add_line_numbers_to_script(updated_script)

    return updated_script


def parse_github_url(github_url: str) -> dict[str, str]:
    """
    Parse a GitHub URL and return the owner and repository name.
    """
    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()

    return {
        "owner": owner,
        "repo": repo
    }


def run_pylint(code_string: str) -> str:
    """
    Lints a string of Python code and returns the Pylint output.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as temp_file:
        temp_file.write(code_string)
        temp_file_path = temp_file.name

    old_stdout = sys.stdout
    string_io = StringIO()
    sys.stdout = string_io

    try:
        lint.Run([temp_file_path], exit=False)
        pylint_output = string_io.getvalue()
    finally:
        sys.stdout = old_stdout
        Path(temp_file_path).unlink()

    return pylint_output


def determine_sampling_frequency(timestamps: list[datetime]) -> str:

    if not timestamps or len(timestamps) < 2:
        raise ValueError(
            "At least 2 timestamps are required to determine sampling frequency")

    # Sort timestamps to ensure proper order
    sorted_timestamps = sorted(timestamps)

    # Calculate time differences between consecutive timestamps
    time_diffs = []
    for i in range(1, len(sorted_timestamps)):
        diff = sorted_timestamps[i] - sorted_timestamps[i-1]
        time_diffs.append(diff.total_seconds())

    # Check if all differences are the same (regular sampling)
    if len(set(time_diffs)) == 1:
        # Regular sampling - determine the frequency
        avg_diff_seconds = time_diffs[0]

        # Convert to different time units and find the most appropriate
        if avg_diff_seconds < 60:  # Less than 1 minute
            return "irr"  # Irregular for sub-minute intervals
        elif avg_diff_seconds < 3600:  # Less than 1 hour
            minutes = avg_diff_seconds / 60
            if minutes.is_integer():
                return "m"
            else:
                return "irr"
        elif avg_diff_seconds < 86400:  # Less than 1 day
            hours = avg_diff_seconds / 3600
            if hours.is_integer():
                return "h"
            else:
                return "irr"
        elif avg_diff_seconds < 604800:  # Less than 1 week
            days = avg_diff_seconds / 86400
            if days.is_integer():
                return "d"
            else:
                return "irr"
        elif avg_diff_seconds < 31536000:  # Less than 1 year
            weeks = avg_diff_seconds / 604800
            if weeks.is_integer():
                return "w"
            else:
                return "irr"
        else:  # 1 year or more
            years = avg_diff_seconds / 31536000
            if years.is_integer():
                return "y"
            else:
                return "irr"
    else:
        # Irregular sampling
        return "irr"


def determine_timezone(timestamps: list[datetime]) -> str:

    if not timestamps:
        raise ValueError(
            "At least 1 timestamp is required to determine timezone")

    # Extract timezone info from each timestamp
    timezones = set()
    for ts in timestamps:
        if ts.tzinfo is None:
            # If timestamp is naive, assume UTC
            timezones.add("UTC")
        else:
            # Get timezone name
            tz_name = ts.tzinfo.tzname(ts)
            if tz_name is None:
                # Fallback to timezone offset
                offset = ts.tzinfo.utcoffset(ts)
                if offset is not None:
                    hours = int(offset.total_seconds() / 3600)
                    tz_name = f"UTC{hours:+03d}:00"
                else:
                    tz_name = "UTC"
            timezones.add(tz_name)

    # Check if all timestamps have the same timezone
    if len(timezones) > 1:
        raise ValueError(
            f"Multiple timezones detected in timestamps: {timezones}")

    # Return the single timezone
    return list(timezones)[0]
