import re
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass
from typing import List, Tuple
import uuid

from project_server.utils import run_python_function_in_container
from project_server.agents.analysis.prompt import ANALYSIS_HELPER_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model
from synesis_schemas.main_server import Dataset, DataSource
from project_server.app_secrets import ANALYSIS_DIR

model = get_model()


@dataclass
class HelperAgentDeps:
    datasets: List[Dataset]
    data_sources: List[DataSource]
    bearer_token: str
    analysis_object_id: uuid.UUID
    analysis_result_id: uuid.UUID


analysis_helper_agent = Agent(
    model,
    system_prompt=ANALYSIS_HELPER_SYSTEM_PROMPT,
    name="Analysis Helper Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3,
    deps_type=HelperAgentDeps
)


@analysis_helper_agent.tool()
async def run_python_code(ctx: RunContext[HelperAgentDeps], python_code: str, output_variable: str) -> str:
    """
    Run python code in a container and return the output.
    Args:
        ctx: The context of the agent.
        python_code: The python code to run.
        output_variable: The output variable of the analysis. This variable is likely the last variable in the code.
    Returns:
        The output of the python code.
    """
    python_code = re.sub(r'\s*print\((.*?)\)\s*\n?', '', python_code)

    python_code = python_code + f"""\n
if isinstance({output_variable}, float) or isinstance({output_variable}, int) or isinstance({output_variable}, str):
    print({output_variable})
elif isinstance({output_variable}, pd.DataFrame) or isinstance({output_variable}, pd.Series):
    if {output_variable}.shape[0] > 10 or {output_variable}.shape[1] > 10:
        print("DataFrame is too large to print. Here are the 10 first and last rows and columns:")
        print("First 10:", {output_variable}.head(10))
        print("Last 10:", {output_variable}.tail(10))
    else:
        print({output_variable})
else:
    print("Not a DataFrame or Series")
"""
    out, err = await _save_data_to_analysis_dir(python_code, output_variable, ctx.deps.analysis_object_id, ctx.deps.analysis_result_id, ctx.deps.bearer_token)

    if err:
        return f"You got the following error: {err}"

    return out


async def _save_data_to_analysis_dir(
    python_code: str,
    output_variable: str,
    analysis_object_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
    bearer_token: str,
) -> Tuple[str, str]:

    assert output_variable in python_code, "output_variable must be in the code"

    out, err = await run_python_function_in_container(
        base_script=(
            f"{python_code}\n\n" +
            "from project_server.entity_manager import LocalDatasetManager\n\n" +
            "from uuid import UUID\n\n" +
            f"dataset_manager = LocalDatasetManager('{bearer_token}')"
        ),
        function_name="dataset_manager.upload_analysis_output_to_analysis_dir",
        input_variables=[
            f"analysis_object_id='{analysis_object_id}'",
            f"analysis_result_id='{analysis_result_id}'",
            f"output_data={output_variable}",
        ],
        print_output=False,
        async_function=True
    )

    return out, err
