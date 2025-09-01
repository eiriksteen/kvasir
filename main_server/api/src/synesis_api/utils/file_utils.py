import asyncio
from pathlib import Path
from typing import List


async def copy_file_or_directory_to_container(
        path: Path,
        container_save_path: Path,
        container_name: str = "synesis-sandbox"):
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
