import json
import uuid
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.data_integration.deps import DataIntegrationAgentDeps
from project_server.utils.code_utils import run_python_function_in_container, remove_print_statements_from_code


class DataIntegrationAgentOutput(BaseModel):
    summary: str
    code_explanation: str
    code: str


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

    if not result.code.strip():
        raise ModelRetry("You didn't provide any code!")

    elif "dataset_create" not in result.code:
        raise ModelRetry(
            "You didn't provide the dataset_create variable in your code!")

    result.code = remove_print_statements_from_code(result.code)

    out, err = await run_python_function_in_container(
        base_script=(
            f"{result.code}\n\nfrom project_server.dataset_manager.local.local_dataset_manager import LocalDatasetManager\n\n" +
            "from uuid import UUID\n\n" +
            f"dataset_manager = LocalDatasetManager('{ctx.deps.bearer_token}')"
        ),
        function_name="dataset_manager.upload_dataset",
        input_variables=[
            "dataset_create",
            repr([ds.id for ds in ctx.deps.data_sources]),
            "[]",
            "[]",
            "True"],
        print_output=True,
        async_function=True
    )

    if err:
        raise ModelRetry(f"Error submitting dataset to API: {err}")

    output_obj = json.loads(out)

    return DataIntegrationAgentOutputWithDatasetId(
        **result.model_dump(),
        dataset_id=output_obj["id"]
    )
