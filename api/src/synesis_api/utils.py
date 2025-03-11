import asyncio
import json
import re
from pathlib import Path
from typing import Tuple, List
import pandas as pd


async def run_code_in_container(python_code: str, container_name: str = "synesis-sandbox") -> Tuple[str, str]:
    """
    Helper function that actually runs Python code inside a Docker container named `sandbox` (by default).
    This is an async version that uses asyncio.create_subprocess_exec for non-blocking execution.
    """
    python_code_stripped = python_code.strip('"""')

    cmd = [
        "docker", "exec", "-i",
        container_name,
        "python", "-c", "import sys; exec(sys.stdin.read())"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate(python_code_stripped.encode('utf-8'))

    # Decode the bytes output back to strings
    return out.decode('utf-8'), err.decode('utf-8')


async def copy_file_to_container(
        file_path: Path,
        target_dir: str = "/tmp",
        container_name: str = "synesis-sandbox"):
    """
    Copy a file to the container.
    """
    cmd = [
        "docker", "cp", file_path, f"{container_name}:{target_dir}/{file_path.name}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode('utf-8'), err.decode('utf-8')


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
