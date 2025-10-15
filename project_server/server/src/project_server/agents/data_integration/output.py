import json
import uuid
from typing import List
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.data_integration.deps import DataIntegrationAgentDeps
from project_server.agents.data_integration.sandbox_code import submit_dataset_to_api
from project_server.utils.code_utils import remove_print_statements_from_code
from synesis_data_structures.time_series.definitions import get_first_level_structure_ids


class ObjectGroupDescription(BaseModel):
    structure_id: str
    variable_name_on_code: str
    description: str
    required: bool


class DataIntegrationAgentOutput(BaseModel):
    summary: str
    code_explanation: str
    code: str
    object_groups: List[ObjectGroupDescription]


class DataIntegrationAgentOutputWithDatasetId(DataIntegrationAgentOutput):
    dataset_id: uuid.UUID


async def submit_data_integration_output(
        ctx: RunContext[DataIntegrationAgentDeps],
        result: DataIntegrationAgentOutput
) -> DataIntegrationAgentOutputWithDatasetId:
    """
    Submit the restructured data to the database.

    Args:
        _: The context.
        result: The result of the integration agent.
    """

    if not result.object_groups:
        raise ModelRetry("You didn't provide any object groups!")

    first_level_structure_ids = get_first_level_structure_ids()
    if any(og.structure_id not in first_level_structure_ids for og in result.object_groups):
        raise ModelRetry(
            f"You didn't provide any valid object groups! Valid structures: {first_level_structure_ids}")

    if not result.code.strip():
        raise ModelRetry("You didn't provide any code!")

    elif "dataset_create" not in result.code:
        raise ModelRetry(
            "You didn't provide the dataset_create variable in your code!")

    result.code = remove_print_statements_from_code(result.code)
    out, err = await submit_dataset_to_api(result.code, ctx.deps.bearer_token, [ds.id for ds in ctx.deps.data_sources])

    if err:
        raise ModelRetry(f"Error submitting dataset to API: {err}")

    output_obj = json.loads(out)

    return DataIntegrationAgentOutputWithDatasetId(
        **result.model_dump(),
        dataset_id=output_obj["id"]
    )
