import asyncio
from pathlib import Path
from typing import List
import re
import pandas as pd
from datetime import datetime, timedelta
from project_server.utils.code_utils import run_python_code_in_container
from pandas.api.types import (
    is_integer_dtype,
    is_float_dtype,
    is_string_dtype,
    is_bool_dtype, 
    is_datetime64_any_dtype, 
    is_timedelta64_dtype
)
import json


async def copy_file_or_directory_to_container(
        path: Path,
        container_save_path: Path,
        container_name: str = "project-sandbox"):
    """
    Copy a file or directory to the container.
    """
    cmd = [
        "docker", "cp", path, f"{container_name}:{container_save_path.as_posix()}"
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
        container_name: str = "project-sandbox"):
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
        container_name: str = "project-sandbox"):
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
        container_name: str = "project-sandbox"):
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


def list_directory_contents(data_directory: Path):
    """
    List the contents of the directory.

    Args:
        ctx: The context
    """

    all_paths = data_directory.glob("**/*")
    visible_paths = [p for p in all_paths if not any(
        part.startswith(".") for part in p.parts)]
    relative_paths = [str(p.relative_to(data_directory))
                      for p in visible_paths]

    return "\n".join(relative_paths)


def resolve_path_from_directory_name(directory_name: str, search_path: Path) -> Path:
    """
    Resolve the path from the directory name by searching through all directory names in the search_path.

    Args:
        directory_name: The name of the directory.
        search_path: The path to search through.
    """

    for path in search_path.glob("**/*"):
        if path.name == directory_name:
            return path

    raise ValueError(
        f"Directory name {directory_name} not found in {search_path}")


def get_path_from_filename(filename: str, paths: List[Path]) -> Path:
    """
    Get the directory from the filename by searching through all directory names in the search_path.

    Args:
        filename: The name of the filename.
        dirs: The list of directories to search through.
    """

    matches = [p for p in paths if filename == p.name]
    assert len(
        matches) == 1, f"Multiple or no files found with name {filename} in {paths}"
    return matches[0]


def simplify_dtype(dtype):
    if is_integer_dtype(dtype):
        return "int"
    elif is_float_dtype(dtype):
        return "float"
    elif is_bool_dtype(dtype):
        return "bool"
    elif is_datetime64_any_dtype(dtype):
        return "datetime"
    elif is_timedelta64_dtype(dtype):
        return "timedelta"
    elif is_string_dtype(dtype) or dtype == object:
        return "str"
    elif dtype == "pd.DataFrame" or dtype == "pd.Series":
        return dtype
    else:
        print(dtype)
        print("here things goes wrong")
        raise ValueError(f"Invalid dtype: {dtype}")

async def get_data_from_container_from_code(python_code: str, variable_name: str) -> pd.DataFrame | pd.Series | float | int | str | bool | datetime | timedelta:
    parquet_filename = 'data_transfer.parquet'
    json_filename = 'data_transfer.json'

    python_code = re.sub(r'\s*print\((.*?)\)\s*\n?', '', python_code)
    python_code = python_code + f"""
import json
from datetime import datetime, timedelta
import pandas as pd
if {variable_name} is None:
    print("ValueErrror, None")
elif isinstance({variable_name}, float) or isinstance({variable_name}, int) or isinstance({variable_name}, str) or isinstance({variable_name}, bool) or isinstance({variable_name}, datetime) or isinstance({variable_name}, timedelta):
    if isinstance({variable_name}, datetime):
        {variable_name} = {variable_name}.isoformat()
        print("datetime")
    elif isinstance({variable_name}, timedelta):
        {variable_name} = {variable_name}.total_seconds()
        print("timedelta")
    else:
        print(type({variable_name}).__name__)
    with open('/tmp/{json_filename}', 'w') as f:
        json.dump({variable_name}, f, default=str)
elif isinstance({variable_name}, pd.DataFrame):
    {variable_name}.to_parquet('/tmp/{parquet_filename}')
    print("pd.DataFrame")
elif isinstance({variable_name}, pd.Series):
    if {variable_name}.name is None:
        df = {variable_name}.to_frame(name='series')
    else:
        df = {variable_name}.to_frame()
    df.to_parquet('/tmp/{parquet_filename}')
    print("pd.DataFrame")
"""
    out1, err1 = await run_python_code_in_container(python_code)

    out1 = simplify_dtype(out1.strip())

    if err1:
        raise err1
    if out1 == "ValueError, None":
        raise ValueError("Variable is None")
    elif out1 == "pd.DataFrame" or out1 == "pd.Series":
        target_path = Path("/tmp") / parquet_filename
    elif out1 == "float" or out1 == "int" or out1 == "str" or out1 == "bool" or out1 == "datetime" or out1 == "timedelta":
        target_path = Path("/tmp") / json_filename
    else:
        raise ValueError("Invalid output type")
    
    host_path = Path("/tmp")
    host_path.mkdir(exist_ok=True)
    host_path = target_path
    
    _, err2 = await copy_file_from_container(target_path, host_path)
    if err2:
        raise err2
    
    if out1 == "pd.DataFrame" or out1 == "pd.Series":
        return pd.read_parquet(host_path)   
    elif out1 == "float" or out1 == "int" or out1 == "str" or out1 == "bool" or out1 == "datetime" or out1 == "timedelta":
        with open(host_path, 'r') as f:
            data = json.load(f)
        if out1 == "float":
            data = float(data)
        elif out1 == "int":
            data = int(data)
        elif out1 == "str":
            data = str(data)
        elif out1 == "bool":
            data = bool(data)
        elif out1 == "datetime":
            data = pd.to_datetime(data)
        elif out1 == "timedelta":
            data = pd.to_timedelta(data, unit='seconds')
  
    return data