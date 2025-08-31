import asyncio
from pathlib import Path


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
