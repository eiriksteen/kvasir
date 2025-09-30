import uuid
from pathlib import Path

from project_server.app_secrets import RAW_DATA_DIR, SCRIPTS_DIR, SCRIPTS_MODULE, SCRIPTS_MODULE_TMP


class FileManager:

    # TODO: Add support for other file types
    def save_raw_data_file(self, file_id: uuid.UUID, filename: str, file_content: bytes) -> Path:
        file_path = RAW_DATA_DIR / f"{file_id}" / f"{filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    def get_raw_data_file_path(self, file_id: uuid.UUID) -> Path:

        if not (RAW_DATA_DIR / f"{file_id}").exists():
            raise FileNotFoundError(
                f"Directory {RAW_DATA_DIR / f"{file_id}"} does not exist")

        if len(list((RAW_DATA_DIR / f"{file_id}").iterdir())) > 1:
            raise FileNotFoundError(
                f"Multiple files found in directory {RAW_DATA_DIR / f"{file_id}"}")

        return list((RAW_DATA_DIR / f"{file_id}").iterdir())[0]

    def delete_raw_data_file(self, file_id: uuid.UUID) -> None:
        file_path = RAW_DATA_DIR / f"{file_id}"

        for file in file_path.iterdir():
            file.unlink()

        file_path.rmdir()

    def save_pipeline_script(self, pipeline_name: str, script_content: str) -> Path:
        # We have a unique index on the function name, so we can use it to save the script
        base_dir = SCRIPTS_DIR / "pipelines"
        base_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{pipeline_name}_{uuid.uuid4()}.py"
        file_path = base_dir / filename
        file_path.write_text(script_content)

        return file_path

    def save_function_script(self, function_name: str, script_content: str, version: int, is_temporary: bool = False, is_setup: bool = False) -> Path:
        # We have a unique index on the function name, so we can use it to save the script
        base_dir = SCRIPTS_DIR / \
            "functions" if not is_temporary else SCRIPTS_DIR / "functions_tmp"
        base_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{function_name}_v{version}.py" if not is_setup else f"{function_name}_v{version}_setup.sh"
        file_path = base_dir / filename
        file_path.write_text(script_content)

        return file_path

    def save_data_integration_script(self, data_integration_id: uuid.UUID, filename: str, script_content: str) -> Path:
        file_path = SCRIPTS_DIR / "data_integration" / \
            f"{data_integration_id}" / f"{filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(script_content)

        return file_path

    def get_function_script_path(self, function_name: str, version: int, is_temporary: bool = False) -> Path:
        base_dir = SCRIPTS_DIR / \
            "functions" if not is_temporary else SCRIPTS_DIR / "functions_tmp"
        return base_dir / f"{function_name}_v{version}.py"

    def get_function_script_module(self, function_name: str, version: int, is_temporary: bool = False) -> str:
        module = SCRIPTS_MODULE if not is_temporary else SCRIPTS_MODULE_TMP
        return f"{module}.{function_name}_v{version}.py"

    def delete_function_script(self, function_name: str, version: int, is_temporary: bool = False) -> None:
        file_path = self.get_function_script_path(
            function_name, version, is_temporary=is_temporary)
        file_path.unlink(missing_ok=True)


file_manager = FileManager()
