from typing import List, Dict


from synesis_data_interface.structures.time_series.definitions import TIME_SERIES_STRUCTURE
from synesis_data_interface.structures.time_series_aggregation.definitions import TIME_SERIES_AGGREGATION_STRUCTURE


DATA_STRUCTURES = [TIME_SERIES_STRUCTURE, TIME_SERIES_AGGREGATION_STRUCTURE]


def get_first_level_structure_ids() -> List[str]:
    """Get all first level IDs."""
    return [struct.first_level_id for struct in DATA_STRUCTURES]


def get_data_structures_overview() -> Dict[str, str]:
    """Get brief descriptions of all data structures."""
    return {struct.first_level_id: struct.brief_description for struct in DATA_STRUCTURES}


def get_data_structure_description(first_level_id: str) -> str:
    """Get the full description of a data structure by its first level ID."""
    if first_level_id not in get_first_level_structure_ids():
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    struct = next(
        (struct for struct in DATA_STRUCTURES if struct.first_level_id == first_level_id), None)
    if struct is None:
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    return f"First level ID of this data structure: {struct.first_level_id}\n\n{struct.description}"


def get_second_level_ids_for_structure(first_level_id: str) -> List[str]:
    """Get the second level IDs for a specific first level structure."""
    if first_level_id not in get_first_level_structure_ids():
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    struct = next(
        (struct for struct in DATA_STRUCTURES if struct.first_level_id == first_level_id), None)
    if struct is None:
        raise ValueError(f"Unknown first level ID: {first_level_id}")

    return struct.second_level_ids
