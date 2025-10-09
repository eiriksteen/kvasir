from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from project_server.utils import run_python_code_in_container, copy_file_or_directory_to_container
from project_server.agents.analysis.prompt import ANALYSIS_HELPER_SYSTEM_PROMPT
import re
from pathlib import Path
from project_server.app_secrets import RAW_DATA_DIR, INTEGRATED_DATA_DIR
from dataclasses import dataclass
import uuid
from project_server.utils.pydanticai_utils import get_model

model = get_model()

@dataclass
class HelperAgentDeps:
    user_id: str
    dataset_ids: list[uuid.UUID]
    group_ids: list[uuid.UUID]
    second_level_structure_ids: list[str]
    data_source_ids: list[uuid.UUID]
    data_source_names: list[str]

analysis_helper_agent = Agent(
    model,
    system_prompt=ANALYSIS_HELPER_SYSTEM_PROMPT,
    name="Analysis Helper Agent",
    model_settings=ModelSettings(temperature=0.1),
    retries=3,
    deps_type=HelperAgentDeps
)

@analysis_helper_agent.tool
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
    if len(ctx.deps.dataset_ids) > 0:
        for idx, (dataset_id, group_id, second_level_structure_id) in enumerate(zip(ctx.deps.dataset_ids, ctx.deps.group_ids, ctx.deps.second_level_structure_ids)):
            file_path = INTEGRATED_DATA_DIR / \
                f"{ctx.deps.user_id}" / \
                f"{dataset_id}" / \
                f"{group_id}" / \
                f"{second_level_structure_id}.parquet"

            container_save_path = Path("/tmp") / f"dataset_{idx}.parquet"

            out, err = await copy_file_or_directory_to_container(file_path, container_save_path)
            if err:
                raise ValueError(f"Error copying file to container: {err}")

    if len(ctx.deps.data_source_ids) > 0:
        for idx, (datasource_id, datasource_name) in enumerate(zip(ctx.deps.data_source_ids, ctx.deps.data_source_names)):
            file_path = RAW_DATA_DIR / \
                f"{ctx.deps.user_id}" / \
                f"{datasource_id}" / \
                f"{datasource_name}"


            container_save_path = Path("/tmp") / f"data_source_{idx}.csv"

            out, err = await copy_file_or_directory_to_container(file_path, container_save_path)
            if err:
                raise ValueError(f"Error copying file to container: {err}")
    
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
from pathlib import Path
Path("{container_save_path}").unlink()
"""
    stdout, stderr = await run_python_code_in_container(python_code)
    if stderr:
        return f"You got the following error: {stderr}"
    return stdout