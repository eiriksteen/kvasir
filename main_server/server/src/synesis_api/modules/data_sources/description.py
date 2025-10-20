from typing import Union, Optional

from synesis_schemas.main_server import (
    DataSourceInDB,
    TabularFileDataSourceInDB,
    KeyValueFileDataSourceInDB,
    DataSourceAnalysisInDB,
)


def get_data_source_description(data_source_in_db: DataSourceInDB,
                                type_fields: Optional[Union[TabularFileDataSourceInDB,
                                                            KeyValueFileDataSourceInDB]] = None,
                                analysis: Optional[DataSourceAnalysisInDB] = None) -> str:
    """
    Generate a comprehensive description of a data source for use in prompts or displays.

    Args:
        data_source: Either a DataSourceInDB or TabularFileDataSource instance

    Returns:
        A formatted string description of the data source
    """
    # Basic information that's always available
    description = f"Data Source: {data_source_in_db.name}\n"
    description += f"- ID: {data_source_in_db.id}\n"
    description += f"- Type: {data_source_in_db.type}\n"
    description += f"- Created: {data_source_in_db.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    # Check if we have the detailed type-specific data source

    if type_fields:
        if isinstance(type_fields, TabularFileDataSourceInDB):
            description += f"\nFile Information:\n"
            description += f"- File Name: {type_fields.file_name}\n"
            description += f"- File Type: {type_fields.file_type}\n"
            description += f"- File Size: {type_fields.file_size_bytes:,} bytes\n"
            description += f"- Dimensions: {type_fields.num_rows:,} rows × {type_fields.num_columns} columns\n"

            # Schema information
            if type_fields.json_schema:
                description += f"\nSchema:\n"
                for field_name, field_info in type_fields.json_schema.items():
                    description += f"- {field_name}: {field_info}\n"

            # Content preview if available
            if type_fields.content_preview:
                description += f"\nPreview:\n{type_fields.content_preview}\n"

        elif isinstance(type_fields, KeyValueFileDataSourceInDB):
            description += f"\nFile Information:\n"
            description += f"- File Name: {type_fields.file_name}\n"
            description += f"- File Type: {type_fields.file_type}\n"
            description += f"- File Size: {type_fields.file_size_bytes:,} bytes\n"

        # Analysis information if available
        if analysis:
            description += f"\nAnalysis:\n"
            description += f"- Content: {analysis.content_description}\n"
            description += f"- Quality: {analysis.quality_description}\n"
            description += f"- EDA Summary: {analysis.eda_summary}\n"
            if analysis.cautions:
                description += f"- Cautions: {analysis.cautions}\n"

    return description
