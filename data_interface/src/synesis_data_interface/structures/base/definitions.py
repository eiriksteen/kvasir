from typing import List
from dataclasses import dataclass


@dataclass
class DataStructureDefinition:
    """Represents a complete data structure definition with all its components."""
    first_level_id: str
    second_level_ids: List[str]
    description: str
    brief_description: str


FEATURE_INFORMATION_SECOND_LEVEL_ID = "feature_information"
ENTITY_METADATA_SECOND_LEVEL_ID = "entity_metadata"
