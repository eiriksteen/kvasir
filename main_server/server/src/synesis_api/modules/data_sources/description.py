from typing import Union

from synesis_schemas.main_server import (
    DataSourceInDB,
    TabularFileDataSource,
)


def get_data_source_description(data_source_in_db: DataSourceInDB,
                                type_fields: Union[TabularFileDataSource]) -> str:
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

    # Check if we have the detailed TabularFileDataSource
    if isinstance(type_fields, TabularFileDataSource):
        description += f"\nFile Information:\n"
        description += f"- File Name: {type_fields.file_name}\n"
        description += f"- File Type: {type_fields.file_type}\n"
        description += f"- File Size: {type_fields.file_size_bytes:,} bytes\n"
        description += f"- Dimensions: {type_fields.num_rows:,} rows × {type_fields.num_columns} columns\n"

        # Features
        if type_fields.features:
            description += f"\nFeatures ({len(type_fields.features)}):\n"
            for feature in type_fields.features:
                feature_desc = f"- {feature.name} ({feature.type}, {feature.subtype}, {feature.scale})"
                if feature.description:
                    feature_desc += f": {feature.description}"
                if feature.unit:
                    feature_desc += f" [Unit: {feature.unit}]"
                description += feature_desc + "\n"

        # Analysis information if available
        if type_fields.analysis:
            description += f"\nAnalysis:\n"
            description += f"- Content: {type_fields.analysis.content_description}\n"
            description += f"- Quality: {type_fields.analysis.quality_description}\n"
            description += f"- EDA Summary: {type_fields.analysis.eda_summary}\n"
            if type_fields.analysis.cautions:
                description += f"- Cautions: {type_fields.analysis.cautions}\n"

        # Content preview if available
        if type_fields.content_preview:
            description += f"\nPreview:\n{type_fields.content_preview}\n"

    return description
