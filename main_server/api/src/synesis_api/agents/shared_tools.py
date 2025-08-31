from typing import Dict
from pydantic_ai import ModelRetry

from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description


def get_data_structures_overview_tool() -> Dict[str, str]:
    """
    Get an overview of the data structures.
    """

    try:
        data_structures_overview = get_data_structures_overview()
    except Exception as e:
        raise ModelRetry(e)

    return data_structures_overview


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
