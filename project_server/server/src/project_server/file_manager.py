from uuid import UUID
from pathlib import Path

from project_server.app_secrets import RAW_DATA_DIR, SCRIPTS_DIR


class FileManager:

    # TODO: Add support for other file types
    def save_raw_data_file(self, file_id: UUID, filename: str, file_content: bytes) -> Path:
        file_path = RAW_DATA_DIR / f"{file_id}" / f"{filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    def get_raw_data_file_path(self, file_id: UUID) -> Path:

        if not (RAW_DATA_DIR / f"{file_id}").exists():
            raise FileNotFoundError(
                f"Directory {RAW_DATA_DIR / f"{file_id}"} does not exist")

        if len(list((RAW_DATA_DIR / f"{file_id}").iterdir())) > 1:
            raise FileNotFoundError(
                f"Multiple files found in directory {RAW_DATA_DIR / f"{file_id}"}")

        return list((RAW_DATA_DIR / f"{file_id}").iterdir())[0]

    def delete_raw_data_file(self, file_id: UUID) -> None:
        file_path = RAW_DATA_DIR / f"{file_id}"

        for file in file_path.iterdir():
            file.unlink()

        file_path.rmdir()

    def save_function_script(self, function_id: UUID, filename: str, script_content: str) -> Path:
        file_path = SCRIPTS_DIR / "functions" / \
            f"{function_id}" / f"{filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(script_content)

        return file_path

    def save_data_integration_script(self, data_integration_id: UUID, filename: str, script_content: str) -> Path:
        file_path = SCRIPTS_DIR / "data_integration" / \
            f"{data_integration_id}" / f"{filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(script_content)

        return file_path


file_manager = FileManager()
