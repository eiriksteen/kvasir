from uuid import UUID
from pathlib import Path
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Tuple, Optional, Any

from kvasir_research.secrets import CODEBASE_DIR, SANDBOX_PYPROJECT_PATH


def create_empty_project_package_local(project_id: UUID, package_name: str) -> Path:
    project_dir = CODEBASE_DIR / str(project_id)
    project_package_dir = project_dir / package_name

    (project_package_dir / "src" /
     package_name).mkdir(parents=True, exist_ok=True)
    (project_package_dir / "src" / package_name / "__init__.py").touch()

    pyproject_content = SANDBOX_PYPROJECT_PATH.read_text()
    pyproject_content = pyproject_content.replace(
        'name = "sandbox"', f'name = "{package_name}"')
    pyproject_content = pyproject_content.replace(
        'packages = ["sandbox"]', f'packages = ["{package_name}"]')
    (project_package_dir / "pyproject.toml").write_text(pyproject_content)

    return project_package_dir


class AbstractSandbox(ABC):

    @abstractmethod
    def __init__(self, project_id: UUID, package_name: str) -> None:
        self.project_id = project_id
        self.package_name = package_name
        self.workdir = f"/app/{package_name}"

    @abstractmethod
    async def create_container_if_not_exists(self) -> bool:
        pass

    # @abstractmethod
    # async def reload_container(self) -> None:
    #     pass

    @abstractmethod
    async def delete_container_if_exists(self):
        pass

    @abstractmethod
    async def run_python_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        """Returns (stdout, stderr)."""
        pass

    @abstractmethod
    async def run_shell_code(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> Tuple[str, str]:
        """Returns (stdout, stderr)."""
        pass

    @abstractmethod
    async def run_shell_code_streaming(self, code: str, truncate_output: bool = True, max_output_length: int = 20000, timeout: int | None = None) -> AsyncGenerator[Tuple[str, str], None]:
        """Yields (stream_type, content) tuples."""
        pass

    @abstractmethod
    async def read_file(self, path: str, truncate: bool = True, max_output_length: int = 20000) -> str:
        pass

    @abstractmethod
    async def write_file(self, path: str, content: str):
        pass

    @abstractmethod
    async def delete_file(self, path: str):
        """Deletes file or directory."""
        pass

    @abstractmethod
    async def rename_file(self, old_path: str, new_path: str):
        """Renames/moves file or directory."""
        pass

    @abstractmethod
    async def check_file_exists(self, path: str) -> bool:
        pass

    @abstractmethod
    async def get_working_directory(self) -> str:
        """Returns the working directory as a string."""
        pass

    @abstractmethod
    async def list_directory_contents(self, path: Optional[str] = None) -> Tuple[str, str]:
        """Returns (stdout, stderr)."""
        pass

    @abstractmethod
    async def get_folder_structure(self, path: Optional[str] = None, n_levels: int = 5, max_lines: int = 100) -> str:
        """Get folder structure description. Returns formatted string."""
        pass

    def is_subpath(self, child: Path, parent: Path) -> bool:
        try:
            child_resolved = child.resolve()
            parent_resolved = parent.resolve()
            return parent_resolved in child_resolved.parents or child_resolved == parent_resolved
        except (OSError, RuntimeError):
            return False

    def get_pyproject_for_env_description(self) -> str:
        with open(SANDBOX_PYPROJECT_PATH, "r") as f:
            dockerfile_content = f.read()

        return dockerfile_content
