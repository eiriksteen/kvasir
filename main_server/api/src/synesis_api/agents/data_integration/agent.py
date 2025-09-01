import json
from pathlib import Path
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.settings import ModelSettings

from synesis_api.agents.data_integration.deps import DataIntegrationAgentDeps
from synesis_api.agents.data_integration.prompt import DATASET_INTEGRATION_SYSTEM_PROMPT
from synesis_api.agents.shared_tools import (
    execute_python_code,
    get_csv_contents,
    get_json_contents,
    get_excel_contents
)
from synesis_api.agents.shared_tools import get_data_structures_overview_tool, get_data_structure_description_tool
from synesis_api.utils.file_utils import copy_file_or_directory_to_container
from synesis_api.utils.pydanticai_utils import get_model
from synesis_api.utils.code_utils import run_python_function_in_container, remove_print_statements_from_code
from synesis_api.agents.data_integration.output import DataIntegrationAgentOutput, DataIntegrationAgentOutputWithDatasetId


model = get_model()


data_integration_agent = Agent(
    model,
    output_type=DataIntegrationAgentOutput,
    model_settings=ModelSettings(temperature=0),
    tools=[
        execute_python_code,
        get_csv_contents,
        get_json_contents,
        get_excel_contents,
        get_data_structures_overview_tool,
        get_data_structure_description_tool
    ],
    retries=3
)


@data_integration_agent.system_prompt
async def get_system_prompt(ctx: RunContext[DataIntegrationAgentDeps]) -> str:

    for file_path in ctx.deps.file_paths:
        _, err = await copy_file_or_directory_to_container(file_path, container_save_path=Path("/tmp") / file_path.name)

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{DATASET_INTEGRATION_SYSTEM_PROMPT}\n\n" +
        f"The data sources are:\n\n" +
        "\n\n".join(
            [f"Filename: {file_path.name}\nFile path: /tmp/{file_path.name}\nData description: {data_description}"
             for file_path, data_description in zip(ctx.deps.file_paths, ctx.deps.data_source_descriptions)]) + "\n\n" +
        f"The target data description is provided by the user in the prompt. Remember to use the full file path in your code!"
    )

    return sys_prompt


@data_integration_agent.output_validator
async def validate_data_integration(
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

    elif "dataset_dict" not in result.code:
        raise ModelRetry(
            "You didn't provide the dataset_dict variable in your code!")

    result.code = remove_print_statements_from_code(result.code)

    print("DATA INTEGRATION AGENT CODE:\n\n" + result.code)

    out, err = await run_python_function_in_container(
        base_script=result.code,
        function_name="submit_dataset_to_api",
        input_variables=["dataset_dict", f"'{ctx.deps.api_key}'"],
        source_module="sandbox.tools",
        print_output=True
    )

    if err:
        raise ModelRetry(f"Error submitting dataset to API: {err}")

    output_obj = json.loads(out)

    return DataIntegrationAgentOutputWithDatasetId(
        **result.model_dump(),
        dataset_id=output_obj["id"]
    )
