import json
import pandas as pd
from pathlib import Path
from pydantic_ai import ModelRetry, RunContext
from synesis_api.utils import run_python_code_in_container, get_basic_df_info
from synesis_api.agents.data_integration.utils import get_path_from_filename


async def execute_python_code(python_code: str):
    """
    Execute a python code block.

    Args:
        ctx: The context
        python_code: The python code to execute.
    """

    out, err = await run_python_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out


async def get_csv_contents(ctx: RunContext, file_name: str):
    """
    Get the contents of a csv file. 

    Args:
        ctx: The context
        file_name: The name of the csv file. Not the full (absolute) path, just the filename!
    """

    assert hasattr(ctx.deps, "file_paths")
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".csv":
        raise ModelRetry("The file must be a csv file.")

    df = pd.read_csv(path)

    return get_basic_df_info(df)


async def get_json_contents(ctx: RunContext, file_name: str):
    """
    Get the contents of a json file. 

    Args:
        ctx: The context
        file_name: The name of the json file. Not the full (absolute) path, just the filename!
    """

    assert hasattr(ctx.deps, "file_paths")
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".json":
        raise ModelRetry("The file must be a json file.")

    with open(path, "r") as f:
        data = json.load(f)

    return data


async def get_excel_contents(ctx: RunContext, file_name: str):
    """
    Get the contents of an xlsx file, including all sheet names and their contents.
    Returns a dictionary with sheet names as keys and basic info as values.

    Args:
        ctx: The context
        file_name: The name of the xlsx file. Not the full (absolute) path, just the filename!
    """

    assert hasattr(ctx.deps, "file_paths")
    path = get_path_from_filename(Path(file_name).name, ctx.deps.file_paths)

    if path.suffix != ".xlsx":
        raise ModelRetry("The file must be an xlsx file.")

    excel_file = pd.ExcelFile(path)
    result = {}

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        result[sheet_name] = get_basic_df_info(df)

    return result
