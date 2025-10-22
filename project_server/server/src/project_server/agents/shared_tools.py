from typing import Dict, Literal
from pydantic_ai import ModelRetry, RunContext

from project_server.utils.code_utils import run_python_code_in_container
from synesis_data_interface.structures.overview import get_data_structures_overview, get_data_structure_description
from synesis_data_interface.sources.overview import get_data_sources_overview, get_data_source_description
from synesis_schemas.main_server import GetGuidelinesRequest
from project_server.client.requests.knowledge_bank import get_task_guidelines
from synesis_data_interface.structures.synthetic import get_synthetic_data_description


def get_data_structures_overview_tool() -> Dict[str, str]:
    """
    Get an overview of the data structures.
    """

    return get_data_structures_overview()


def get_data_structure_description_tool(first_level_id: str) -> str:
    """
    Get the description of a data structure.
    """

    try:
        data_structure_description = get_data_structure_description(
            first_level_id)
    except Exception as e:
        raise ModelRetry(e)

    return data_structure_description


def get_data_sources_overview_tool() -> str:
    """
    Get an overview of the data sources.
    """
    return get_data_sources_overview()


def get_data_source_description_tool(data_source: str) -> str:
    """
    Get the description of a data source.
    """
    try:
        data_source_description = get_data_source_description(data_source)
    except Exception as e:
        raise ModelRetry(e)

    return data_source_description


async def execute_python_code(python_code: str):
    """
    Execute a python code block.

    Args:
        python_code: The python code to execute.
        explanation: Explanation of what you are doing and why - very concisely.
    """

    out, err = await run_python_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out


async def get_task_guidelines_tool(ctx: RunContext, task: Literal["time_series_forecasting"]) -> str:
    assert hasattr(ctx.deps, "client"), "Client is required"
    return await get_task_guidelines(ctx.deps.client, GetGuidelinesRequest(task=task))


def get_synthetic_data_description_tool(first_level_id: str) -> str:
    return get_synthetic_data_description(first_level_id)
