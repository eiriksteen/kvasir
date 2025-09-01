import json
import pandas as pd
from typing import Dict
from pathlib import Path
from pydantic_ai import ModelRetry, RunContext

from synesis_api.utils.code_utils import run_python_code_in_container
from synesis_api.utils.dataframe_utils import get_basic_df_info
from synesis_api.utils.file_utils import get_path_from_filename
from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description


def get_data_structures_overview_tool() -> Dict[str, str]:
    """
    Get an overview of the data structures.
    """

    try:
        data_structures_overview = get_data_structures_overview()
    except Exception as e:
        raise ModelRetry(e)

    return data_structures_overview


def get_data_structure_description_tool(first_level_id: str) -> str:
    """
    Get the description of a data structure.
    """

    try:
        data_structure_description = get_data_structure_description(
            first_level_id)
    except Exception as e:
        raise ModelRetry(e)

    return data_structure_description


async def execute_python_code(python_code: str, explanation: str):
    """
    Execute a python code block.

    Args:
        ctx: The context
        python_code: The python code to execute.
        explanation: Explanation of what you are doing and why - very concisely.
    """

    # To avoid unused variable warning
    # Explanation is logged to redis
    # We could log here, but right now it is done in the runner
    _ = explanation

    out, err = await run_python_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out


async def get_csv_contents(ctx: RunContext, file_name: str, explanation: str):
    """
    Get the contents of a csv file. 

    Args:
        ctx: The context
        file_name: The name of the csv file. Not the full (absolute) path, just the filename!
        explanation: Explanation of what you are doing and why - very concisely.
    """

    # To avoid unused variable warning
    # Explanation is logged to redis
    # We could log here, but right now it is done in the runner
    _ = explanation

    assert hasattr(ctx.deps, "file_paths"), "file_paths not found in context"
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".csv":
        raise ModelRetry("The file must be a csv file.")

    df = pd.read_csv(path)

    return get_basic_df_info(df)


async def get_json_contents(ctx: RunContext, file_name: str, explanation: str):
    """
    Get the contents of a json file. 

    Args:
        ctx: The context
        file_name: The name of the json file. Not the full (absolute) path, just the filename!
        explanation: Explanation of what you are doing and why - very concisely.
    """

    # To avoid unused variable warning
    # Explanation is logged to redis
    # We could log here, but right now it is done in the runner
    _ = explanation

    assert hasattr(ctx.deps, "file_paths"), "file_paths not found in context"
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".json":
        raise ModelRetry("The file must be a json file.")

    with open(path, "r") as f:
        data = json.load(f)

    return data


async def get_excel_contents(ctx: RunContext, file_name: str, explanation: str):
    """
    Get the contents of an xlsx file, including all sheet names and their contents.
    Returns a dictionary with sheet names as keys and basic info as values.

    Args:
        ctx: The context
        file_name: The name of the xlsx file. Not the full (absolute) path, just the filename!
        explanation: Explanation of what you are doing and why - very concisely.
    """

    # To avoid unused variable warning
    # Explanation is logged to redis
    # We could log here, but right now it is done in the runner
    _ = explanation

    assert hasattr(ctx.deps, "file_paths"), "file_paths not found in context"
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".xlsx":
        raise ModelRetry("The file must be an xlsx file.")

    excel_file = pd.ExcelFile(path)
    result = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        result[sheet_name] = get_basic_df_info(df)

    return result
