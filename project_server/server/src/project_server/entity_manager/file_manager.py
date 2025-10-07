import uuid
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass

from project_server.app_secrets import (
    RAW_DATA_DIR,
    FUNCTIONS_DIR,
    FUNCTIONS_DIR_TMP,
    MODELS_DIR,
    MODELS_DIR_TMP,
    PIPELINES_DIR,
    PIPELINES_DIR_TMP,
    DATA_INTEGRATION_DIR,
    DATA_INTEGRATION_DIR_TMP,
    FUNCTIONS_MODULE,
    FUNCTIONS_MODULE_TMP,
    MODELS_MODULE,
    MODELS_MODULE_TMP,
    PIPELINES_MODULE,
    PIPELINES_MODULE_TMP,
    DATA_INTEGRATION_MODULE,
    DATA_INTEGRATION_MODULE_TMP
)


@dataclass
class ScriptStorage:
    filename: str
    script_path: Path
    module_path: str
    setup_script_path: Optional[Path] = None


class FileManager:

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

    def save_model_script(
            self,
            python_model_name: str,
            script_content: str,
            version: int,
            setup_script_content: Optional[str] = None) -> ScriptStorage:

        filename = f"{python_model_name}_v{version}.py"
        file_path = MODELS_DIR / filename
        file_path.write_text(script_content)

        setup_file_path = None
        if setup_script_content:
            setup_file_path = MODELS_DIR / \
                f"{python_model_name}_v{version}_setup.sh"
            setup_file_path.write_text(setup_script_content)

        module_path = f"{MODELS_MODULE}.{python_model_name}_v{version}"

        return ScriptStorage(filename=filename, script_path=file_path, setup_script_path=setup_file_path, module_path=module_path)

    def save_function_script(
            self,
            python_function_name: str,
            script_content: str,
            version: int,
            setup_script_content: Optional[str] = None) -> ScriptStorage:

        filename = f"{python_function_name}_v{version}.py"
        file_path = FUNCTIONS_DIR / filename
        file_path.write_text(script_content)

        setup_file_path = None
        if setup_script_content:
            setup_file_path = FUNCTIONS_DIR / \
                f"{python_function_name}_v{version}_setup.sh"
            setup_file_path.write_text(setup_script_content)

        module_path = f"{FUNCTIONS_MODULE}.{python_function_name}_v{version}"

        return ScriptStorage(filename=filename, script_path=file_path, setup_script_path=setup_file_path, module_path=module_path)

    def save_pipeline_script(self, python_function_name: str, script_content: str, setup_script_content: Optional[str] = None) -> ScriptStorage:
        # We have a unique index on the function name, so we can use it to save the script
        pipe_uuid = uuid.uuid4()
        filename = f"{python_function_name}_{pipe_uuid}.py"
        file_path = PIPELINES_DIR / filename
        file_path.write_text(script_content)

        setup_file_path = None
        if setup_script_content:
            setup_file_path = PIPELINES_DIR / \
                f"{python_function_name}_{pipe_uuid}_setup.sh"
            setup_file_path.write_text(setup_script_content)

        module_path = f"{PIPELINES_MODULE}.{python_function_name}_{pipe_uuid}"

        return ScriptStorage(filename=filename, script_path=file_path, setup_script_path=setup_file_path, module_path=module_path)

    def save_data_integration_script(
            self,
            data_integration_id: uuid.UUID,
            script_content: str,
            setup_script_content: Optional[str] = None) -> ScriptStorage:

        filename = f"data_integration_{data_integration_id}.py"
        file_path = DATA_INTEGRATION_DIR / filename
        file_path.write_text(script_content)

        setup_file_path = None
        if setup_script_content:
            setup_file_path = DATA_INTEGRATION_DIR / \
                f"data_integration_{data_integration_id}_setup.sh"
            setup_file_path.write_text(setup_script_content)

        module_path = f"{DATA_INTEGRATION_MODULE}.data_integration_{data_integration_id}"

        return ScriptStorage(filename=filename, script_path=file_path, setup_script_path=setup_file_path, module_path=module_path)

    def save_temporary_script(
            self,
            filename: str,
            script_content: str,
            script_type: Literal["function", "model", "pipeline", "data_integration"],
            overwrite: bool = False
    ) -> ScriptStorage:

        if script_type == "function":
            base_dir = FUNCTIONS_DIR_TMP
            base_module = FUNCTIONS_MODULE_TMP
        elif script_type == "model":
            base_dir = MODELS_DIR_TMP
            base_module = MODELS_MODULE_TMP
        elif script_type == "pipeline":
            base_dir = PIPELINES_DIR_TMP
            base_module = PIPELINES_MODULE_TMP
        elif script_type == "data_integration":
            base_dir = DATA_INTEGRATION_DIR_TMP
            base_module = DATA_INTEGRATION_MODULE_TMP

        target_filename = filename if overwrite else f"id_{uuid.uuid4()}_{filename}"
        script_path = base_dir / target_filename
        script_path.write_text(script_content)
        # :-3 to remove the .py extension
        module_path = f"{base_module}.{target_filename[:-3]}"

        return ScriptStorage(filename=target_filename, script_path=script_path, module_path=module_path)

    def delete_temporary_script(self, filename_uuid: str, script_type: Literal["function", "model", "pipeline", "data_integration"]) -> None:
        if script_type == "function":
            base_dir = FUNCTIONS_DIR_TMP
        elif script_type == "model":
            base_dir = MODELS_DIR_TMP
        elif script_type == "pipeline":
            base_dir = PIPELINES_DIR_TMP
        elif script_type == "data_integration":
            base_dir = DATA_INTEGRATION_DIR_TMP

        script_path = base_dir / filename_uuid
        script_path.unlink()


file_manager = FileManager()
