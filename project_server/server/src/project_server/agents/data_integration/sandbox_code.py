import uuid
from typing import List, Tuple

from project_server.utils.code_utils import run_python_function_in_container


async def submit_dataset_to_api(
    code: str,
    bearer_token: str,
    data_source_ids: List[uuid.UUID]
) -> Tuple[str, str]:

    assert "dataset_create" in code, "dataset_create must be in the code"

    out, err = await run_python_function_in_container(
        base_script=(
            f"{code}\n\n" +
            "from project_server.entity_manager import LocalDatasetManager\n\n" +
            "from uuid import UUID\n\n" +
            "from synesis_schemas.main_server import DatasetSources\n\n" +
            f"dataset_manager = LocalDatasetManager('{bearer_token}')"
        ),
        function_name="dataset_manager.upload_dataset",
        input_variables=[
            "dataset_create",
            f"DatasetSources(data_source_ids={repr(data_source_ids)}, dataset_ids=[], pipeline_ids=[])",
            "output_json=True"],
        print_output=True,
        async_function=True
    )

    return out, err
