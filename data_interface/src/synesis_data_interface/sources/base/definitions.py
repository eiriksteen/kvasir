from dataclasses import dataclass


@dataclass
class DataSourceDefinition:
    """Represents a complete data structure definition with all its components."""
    name: str
    description: str
    brief_description: str
