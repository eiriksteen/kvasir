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

UUID_FILENAME_SPLITTER = "_fn_"


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

    def save_script(
            self,
            filename: str,
            script_content: str,
            script_type: Literal["function", "model", "pipeline", "data_integration"],
            add_uuid: bool = False,
            temporary: bool = False,
            add_v1: bool = False,
            increase_version_number: bool = False
    ) -> ScriptStorage:

        if script_type == "function":
            base_dir = FUNCTIONS_DIR_TMP if temporary else FUNCTIONS_DIR
            base_module = FUNCTIONS_MODULE_TMP if temporary else FUNCTIONS_MODULE
        elif script_type == "model":
            base_dir = MODELS_DIR_TMP if temporary else MODELS_DIR
            base_module = MODELS_MODULE_TMP if temporary else MODELS_MODULE
        elif script_type == "pipeline":
            base_dir = PIPELINES_DIR_TMP if temporary else PIPELINES_DIR
            base_module = PIPELINES_MODULE_TMP if temporary else PIPELINES_MODULE
        elif script_type == "data_integration":
            base_dir = DATA_INTEGRATION_DIR_TMP if temporary else DATA_INTEGRATION_DIR
            base_module = DATA_INTEGRATION_MODULE_TMP if temporary else DATA_INTEGRATION_MODULE

        if add_v1:
            assert ".py" in filename, "Filename must end with .py"
            name, _ = filename.split(".py")
            filename = f"{name}_v1.py"

        if increase_version_number:
            assert ".py" in filename, "Filename must end with .py"
            name_with_version, _ = filename.split(".py")

            try:
                fname_underscore_split = name_with_version.split("_")
                version_str = fname_underscore_split[-1]
                version_num = int(version_str[1:])
                name = "_".join(fname_underscore_split[:-1])
            except Exception as e:
                raise ValueError(
                    f"Error extracting version number from filename: {filename}") from e

            filename = f"{name}_v{version_num + 1}.py"

        if add_uuid:
            str_uuid = str(uuid.uuid4()).replace("-", "")
            target_filename = f"id_{str_uuid}{UUID_FILENAME_SPLITTER}{filename}"
        else:
            target_filename = filename

        script_path = base_dir / target_filename
        script_path.write_text(script_content)
        # :-3 to remove the .py extension
        module_path = f"{base_module}.{target_filename[:-3]}"

        return ScriptStorage(filename=target_filename, script_path=script_path, module_path=module_path)

    def delete_temporary_script(self, filename: str) -> None:

        for base_dir in [FUNCTIONS_DIR_TMP, MODELS_DIR_TMP, PIPELINES_DIR_TMP, DATA_INTEGRATION_DIR_TMP]:
            script_path = base_dir / filename
            if script_path.exists():
                script_path.unlink()

    def clean_temporary_script(self, script_content: str) -> str:
        TMP_MODULES = [FUNCTIONS_MODULE_TMP, MODELS_MODULE_TMP,
                       PIPELINES_MODULE_TMP, DATA_INTEGRATION_MODULE_TMP]
        PROD_MODULES = [FUNCTIONS_MODULE, MODELS_MODULE,
                        PIPELINES_MODULE, DATA_INTEGRATION_MODULE]

        for module_idx in range(len(TMP_MODULES)):
            script_content = script_content.replace(
                TMP_MODULES[module_idx], PROD_MODULES[module_idx])

        return script_content


file_manager = FileManager()
