"""
Unified data structures module.

This module provides a unified API for working with different data structures.
Each structure is defined in its own submodule and can be used independently,
but this module provides common functions that work with any structure type.

Usage:
    from synesis_data_interface.structures import (
        generate_synthetic_data,
        validate_object_group_structure,
        serialize_dataframes_to_api_payloads,
        serialize_dataframes_to_parquet
    )
"""

from synesis_data_interface.structures.synthetic import (
    generate_synthetic_data,
    get_synthetic_data_description
)
from synesis_data_interface.structures.validation import (
    validate_object_group_structure
)
from synesis_data_interface.structures.serialization import (
    serialize_dataframes_to_api_payloads,
    serialize_dataframes_to_parquet,
    deserialize_parquet_to_dataframes
)
from synesis_data_interface.structures.overview import (
    get_first_level_structure_ids,
    get_data_structures_overview,
    get_data_structure_description,
    get_second_level_ids_for_structure
)

__all__ = [
    # Synthetic data generation
    'generate_synthetic_data',
    'get_synthetic_data_description',

    # Validation
    'validate_object_group_structure',

    # Serialization
    'serialize_dataframes_to_api_payloads',
    'serialize_dataframes_to_parquet',
    'deserialize_parquet_to_dataframes',

    # Structure metadata
    'get_first_level_structure_ids',
    'get_data_structures_overview',
    'get_data_structure_description',
    'get_second_level_ids_for_structure',
]
