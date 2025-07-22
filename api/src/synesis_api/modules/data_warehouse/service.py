import pandas as pd
from uuid import UUID
from pathlib import Path
from typing import Literal
from synesis_api.secrets import DATASETS_SAVE_PATH, DATA_INTEGRATION_SCRIPTS_PATH, AUTOMATION_SCRIPTS_PATH, ANALYSIS_SCRIPTS_PATH


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
        path = DATA_INTEGRATION_SCRIPTS_PATH / \
            f"{user_id}" / f"{job_id}" / filename
    elif kind == "automation":
        path = AUTOMATION_SCRIPTS_PATH / \
            f"{user_id}" / f"{job_id}" / filename
    elif kind == "analysis":
        path = ANALYSIS_SCRIPTS_PATH / \
            f"{user_id}" / f"{job_id}" / filename

    path.write_text(script)

    return path
