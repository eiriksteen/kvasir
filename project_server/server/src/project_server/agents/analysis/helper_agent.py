import uuid
import re
from pathlib import Path
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from dataclasses import dataclass
from typing import List


from project_server.utils import run_python_code_in_container, copy_file_or_directory_to_container, remove_from_container
from project_server.agents.analysis.prompt import ANALYSIS_HELPER_SYSTEM_PROMPT
from project_server.utils.pydanticai_utils import get_model
from synesis_schemas.main_server import Dataset, DataSourceFull

model = get_model()

@dataclass
class HelperAgentDeps:
    datasets: List[Dataset]
    data_sources: List[DataSourceFull]
    # user_id: str
    # dataset_ids: list[uuid.UUID]
    # group_ids: list[uuid.UUID]
    # second_level_structure_ids: list[str]
    # data_source_ids: list[uuid.UUID]
    # data_source_names: list[str]

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

    
    stdout, stderr = await run_python_code_in_container(python_code)
    if stderr:
        return f"You got the following error: {stderr}"

    return stdout