import pandas as pd
import aiofiles
from uuid import UUID
from pathlib import Path
from typing import Literal, Optional
from datetime import datetime
from fastapi import UploadFile

from synesis_api.secrets import (
    DATASETS_SAVE_PATH,
    DATA_INTEGRATION_SCRIPTS_SAVE_DIR,
    PIPELINE_SCRIPTS_SAVE_DIR,
    ANALYSIS_SCRIPTS_SAVE_DIR,
    RAW_FILES_SAVE_DIR,
)

from synesis_data_structures.time_series.definitions import get_second_level_structure_ids


def save_dataframe_to_local_storage(
    user_id: UUID,
    dataset_id: UUID,
    group_id: UUID,
    dataframe: pd.DataFrame,
    second_level_structure_id: str
) -> None:

    assert second_level_structure_id in get_second_level_structure_ids(
    ), f"Second level structure id {second_level_structure_id} not found in {get_second_level_structure_ids()}       "

    file_path = DATASETS_SAVE_PATH / \
        f"{user_id}" / \
        f"{dataset_id}" / \
        f"{group_id}" / \
        f"{second_level_structure_id}.parquet"

    file_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(file_path, index=True)


def read_dataframe_from_local_storage(
    user_id: UUID,
    dataset_id: UUID,
    group_id: UUID,
    second_level_structure_id: str
) -> pd.DataFrame:

    assert second_level_structure_id in get_second_level_structure_ids(
    ), f"Second level structure id {second_level_structure_id} not found in {get_second_level_structure_ids()}       "

    file_path = DATASETS_SAVE_PATH / \
        f"{user_id}" / \
        f"{dataset_id}" / \
        f"{group_id}" / \
        f"{second_level_structure_id}.parquet"

    dataframe = pd.read_parquet(file_path)

    return dataframe


def save_script_to_local_storage(
    user_id: UUID,
    run_id: UUID,
    script: str,
    filename: str,
    kind: Literal["data_integration", "pipeline", "analysis"]
) -> Path:

    if kind == "data_integration":
        parent_dir = DATA_INTEGRATION_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{run_id}"
    elif kind == "pipeline":
        parent_dir = PIPELINE_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{run_id}"
    elif kind == "analysis":
        parent_dir = ANALYSIS_SCRIPTS_SAVE_DIR / \
            f"{user_id}" / f"{run_id}"

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
