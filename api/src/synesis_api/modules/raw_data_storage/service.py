import pandas as pd
import aiofiles
from uuid import UUID
from pathlib import Path
from typing import Literal
from fastapi import UploadFile
from synesis_api.secrets import (
    DATASETS_SAVE_PATH,
    DATA_INTEGRATION_SCRIPTS_SAVE_DIR,
    AUTOMATION_SCRIPTS_SAVE_DIR,
    ANALYSIS_SCRIPTS_SAVE_DIR,
    RAW_FILES_SAVE_DIR
)


def save_dataframe_to_local_storage(
    user_id: UUID,
    dataset_id: UUID,
    group_id: UUID,
    dataframe: pd.DataFrame,
    second_level_structure_id: str
) -> None:

    file_path = DATASETS_SAVE_PATH / \
        f"{user_id}" / \
        f"{dataset_id}" / \
        f"{group_id}" / \
        f"{second_level_structure_id}.parquet"

    file_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(file_path, index=True)


def save_script_to_local_storage(
    user_id: UUID,
    job_id: UUID,
    script: str,
    filename: str,
    kind: Literal["data_integration", "automation", "analysis"]
) -> Path:

    if kind == "data_integration":
        parent_dir = DATA_INTEGRATION_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{job_id}"
    elif kind == "automation":
        parent_dir = AUTOMATION_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{job_id}"
    elif kind == "analysis":
        parent_dir = ANALYSIS_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{job_id}"

    parent_dir.mkdir(parents=True, exist_ok=True)
    path = parent_dir / filename
    path.write_text(script)

    return path


async def save_raw_file_to_local_storage(
    user_id: UUID,
    file_id: UUID,
    file: UploadFile
) -> Path:

    file_path = RAW_FILES_SAVE_DIR / \
        f"{user_id}" / \
        f"{file_id}" / \
        f"{file.filename}"

    file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, mode="wb") as f:
        await f.write(await file.read())

    return file_path
