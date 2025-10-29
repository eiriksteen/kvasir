from typing import Optional

from synesis_schemas.main_server import (
    DataSourceInDB,
    FileDataSourceInDB,
)


def get_data_source_description(data_source_in_db: DataSourceInDB,
                                type_fields: Optional[FileDataSourceInDB] = None) -> str:
    """
    Generate a comprehensive description of a data source for use in prompts or displays.

    Args:
        data_source_in_db: The base data source record
        type_fields: Optional specific type fields (e.g., FileDataSourceInDB)

    Returns:
        A formatted string description of the data source
    """
    # Basic information that's always available
    description = f"Data Source: {data_source_in_db.name}\n"
    description += f"- ID: {data_source_in_db.id}\n"
    description += f"- Type: {data_source_in_db.type}\n"
    description += f"- Created: {data_source_in_db.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    # Add additional variables if present
    if data_source_in_db.additional_variables:
        description += f"- Additional Variables: {data_source_in_db.additional_variables}\n"

    # Check if we have the detailed type-specific data source
    if type_fields:
        if isinstance(type_fields, FileDataSourceInDB):
            description += f"\nFile Information:\n"
            description += f"- File Name: {type_fields.file_name}\n"
            description += f"- File Path: {type_fields.file_path}\n"
            description += f"- File Type: {type_fields.file_type}\n"
            description += f"- File Size: {type_fields.file_size_bytes:,} bytes\n"

    return description
