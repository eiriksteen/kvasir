import asyncio
import docker
from pathlib import Path
from uuid import UUID
from docker.errors import NotFound, ImageNotFound

from project_server.app_secrets import (
    SANDBOX_DIR,
    SANDBOX_PYPROJECT_PATH,
    SANDBOX_HOST_DIR,
    PROJECT_SERVER_HOST_DIR,
    SCHEMAS_HOST_DIR
)

from synesis_schemas.main_server import Project
from project_server.utils.code_utils import run_shell_code_in_container


async def _install_package_after_start(container_name: str, project: Project) -> None:
    _, err = await run_shell_code_in_container(
        "pip install -e .",
        container_name,
        cwd=f"/app/{project.python_package_name}"
    )

    if err:
        raise RuntimeError(
            f"Failed to install package in container: {err}")


async def create_project_container_if_not_exists(project: Project, image_name: str = "sandbox") -> None:
    docker_client = docker.from_env()
    container_name = str(project.id)

    try:
        existing_container = docker_client.containers.get(container_name)
        if existing_container.status != "running":
            existing_container.start()
            await _install_package_after_start(container_name, project)
    except NotFound:
        project_dir = SANDBOX_HOST_DIR / str(project.id)
        project_package_dir = project_dir / project.python_package_name

        if not project_dir.exists():
            _create_empty_project_package(project)

        try:
            docker_client.images.get(image_name)
        except ImageNotFound as e:
            raise RuntimeError(
                f"Sandbox image {image_name} not found, the image must be built first") from e

        container = docker_client.containers.create(
            image=image_name,
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            working_dir=f"/app/{project.python_package_name}",
            volumes={str(project_package_dir): {"bind": f"/app/{project.python_package_name}", "mode": "rw"},
                     # Crucial - Read only for external code, we don't want the agent to mess with this
                     str(SCHEMAS_HOST_DIR): {"bind": "/app/schemas", "mode": "ro"},
                     str(PROJECT_SERVER_HOST_DIR): {"bind": "/app/server", "mode": "ro"}}
        )
        container.start()
        await _install_package_after_start(container_name, project)


def _create_empty_project_package(project: Project) -> None:
    """Create directory structure, pyproject.toml, and Dockerfile for first-time project setup"""
    project_dir = SANDBOX_DIR / str(project.id)
    project_package_dir = project_dir / project.python_package_name

    (project_package_dir / "src" /
     project.python_package_name).mkdir(parents=True, exist_ok=True)
    (project_package_dir / "src" / project.python_package_name / "__init__.py").touch()

    pyproject_content = SANDBOX_PYPROJECT_PATH.read_text()
    pyproject_content = pyproject_content.replace(
        'name = "sandbox"', f'name = "{project.python_package_name}"')
    pyproject_content = pyproject_content.replace(
        'packages = ["sandbox"]', f'packages = ["{project.python_package_name}"]')
    (project_package_dir / "pyproject.toml").write_text(pyproject_content)


def delete_project_container_if_exists(project: Project) -> None:
    docker_client = docker.from_env()
    container_name = str(project.id)

    existing_container = docker_client.containers.get(container_name)
    if existing_container:
        existing_container.stop()
        existing_container.remove()


async def ensure_directory_exists(
        directory_path: str,
        container_name: str):
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"mkdir -p {directory_path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to create directory in container: {err.decode('utf-8')}")

    return out.decode("utf-8")


async def copy_file_or_directory_to_container(
        path: Path,
        container_save_path: Path,
        container_name: str):
    parent_dir = container_save_path.parent

    # Create parent directory if it doesn't exist
    mkdir_cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"mkdir -p {parent_dir}"
    ]

    mkdir_process = await asyncio.create_subprocess_exec(
        *mkdir_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    _, mkdir_err = await mkdir_process.communicate()

    if mkdir_process.returncode != 0:
        raise RuntimeError(
            f"Failed to create directory in container: {mkdir_err.decode('utf-8')}")

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

    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to copy file or directory to container: {err.decode('utf-8')}")

    return out.decode("utf-8")


async def copy_file_from_container(
        file_path: Path,
        container_name: str,
        target_dir: str = "/tmp"):
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

    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to copy file from container: {err.decode('utf-8')}")

    return out.decode("utf-8")


async def write_file_to_container(
        path: Path,
        content: str,
        container_name: str):
    """
    Create a file in the container with the given content.
    Ensures the directory exists and creates the file before writing.
    """
    escaped_content = content.replace("'", "'\\''")

    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"mkdir -p $(dirname {path}) && touch {path} && echo '{escaped_content}' > {path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to write file to container: {err.decode('utf-8')}")

    return out.decode("utf-8")


async def read_file_from_container(
        path: Path,
        container_name: str):
    """
    Read a file from the container.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"cat {path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to read file from container: {err.decode('utf-8')}")

    return out.decode("utf-8")


async def check_file_exists_in_container(
        path: Path,
        container_name: str) -> bool:
    """
    Check if a file exists in the container.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "bash", "-c", f"test -f {path} && echo 'exists' || echo 'not_exists'"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8").strip() == "exists"


async def remove_from_container(
        directory_path: Path,
        container_name: str):
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


async def rename_in_container(
        old_path: Path,
        new_path: Path,
        container_name: str):
    """
    Rename/move a file or directory in the container.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "mv", f"{old_path}", f"{new_path}"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


async def list_container_working_directory_contents(
        container_name: str):
    """
    List the contents of the working directory of the container.
    """
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "ls", "-la"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")


async def get_container_working_directory(container_name: str):
    cmd = [
        "docker", "exec", "-i",
        container_name,
        "pwd"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()

    return out.decode("utf-8"), err.decode("utf-8")
