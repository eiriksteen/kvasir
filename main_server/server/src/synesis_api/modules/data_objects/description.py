from typing import List


# Import description functions
from synesis_api.modules.data_sources.description import get_data_source_description
from synesis_api.modules.pipeline.description import get_pipeline_description
from synesis_schemas.main_server import DatasetInDB, ObjectGroup


def get_dataset_description(dataset_in_db: DatasetInDB,
                            object_groups: List[ObjectGroup],
                            include_full_data_source_description: bool = True,
                            include_full_pipeline_description: bool = True) -> str:
    """
    Generate a comprehensive description of a dataset for LLM consumption.

    Args:
        dataset_in_db: The dataset database record
        object_groups: List of object groups in the dataset
        include_full_data_source_description: Whether to include detailed data source descriptions
        include_full_pipeline_description: Whether to include detailed pipeline descriptions

    Returns:
        A formatted string description suitable for LLM prompts
    """
    lines = [
        f"## Dataset: {dataset_in_db.name} (ID: {dataset_in_db.id})",
        f"**Description:** {dataset_in_db.description}",
        f"**Created:** {dataset_in_db.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Updated:** {dataset_in_db.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Include additional variables from dataset
    if dataset_in_db.additional_variables:
        lines.append("### Dataset Additional Variables")
        for key, value in dataset_in_db.additional_variables.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    if object_groups:
        lines.append("### Object Groups")
        lines.append("")

        for object_group in object_groups:
            lines.append(f"#### {object_group.name} (ID: {object_group.id})")
            lines.append(f"**Type:** {object_group.modality}")
            lines.append(f"**Description:** {object_group.description}")
            lines.append(
                f"**Created:** {object_group.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            # Include additional variables from object group
            if object_group.additional_variables:
                lines.append("**Additional Variables:**")
                for key, value in object_group.additional_variables.items():
                    lines.append(f"- **{key}:** {value}")
                lines.append("")

            # Data Sources for this object group
            if object_group.sources.data_sources:
                lines.append(
                    "**Data sources that provide data for this object group:**")
                for data_source in object_group.sources.data_sources:
                    if include_full_data_source_description:
                        lines.append("```")
                        lines.append(get_data_source_description(
                            data_source,
                            data_source.type_fields,
                            data_source.analysis
                        ))
                        lines.append("```")
                    else:
                        lines.append(
                            f"- **{data_source.name}** (ID: {data_source.id}, Type: {data_source.type})")
                        lines.append(
                            f"  - File Path: `{data_source.type_fields.file_path}`")
                        lines.append(
                            f"  - File Type: {data_source.type_fields.file_type}")
                        if hasattr(data_source.type_fields, 'num_rows'):
                            lines.append(
                                f"  - Dimensions: {data_source.type_fields.num_rows:,} rows × {data_source.type_fields.num_columns} columns")
                lines.append("")

            # Pipelines for this object group
            if object_group.sources.pipelines:
                lines.append("**Pipelines that create this object group:**")
                for pipeline in object_group.sources.pipelines:
                    if include_full_pipeline_description:
                        lines.append("```")
                        lines.append(get_pipeline_description(pipeline))
                        lines.append("```")
                    else:
                        lines.append(
                            f"- **{pipeline.name}** (ID: {pipeline.id})")
                        if pipeline.description:
                            lines.append(
                                f"  Description: {pipeline.description}")
                lines.append("")

            # Data structure information based on modality
            if object_group.modality == "time_series":
                lines.append("**Time Series Data Structure:**")

                # Get time series group information
                ts_group = object_group.modality_fields
                lines.append(
                    f"- Total Timestamps: {ts_group.total_timestamps:,}")
                lines.append(
                    f"- Number of Series: {ts_group.number_of_series:,}")
                lines.append(
                    f"- Earliest Timestamp: {ts_group.earliest_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(
                    f"- Latest Timestamp: {ts_group.latest_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

                if ts_group.sampling_frequency:
                    lines.append(
                        f"- Sampling Frequency: {ts_group.sampling_frequency}")
                else:
                    lines.append(
                        f"- Sampling Frequency: Varying between series")
                if ts_group.timezone:
                    lines.append(f"- Timezone: {ts_group.timezone}")
                else:
                    lines.append(f"- Timezone: Varying between series")
                if ts_group.features_schema:
                    lines.append(
                        f"- Features Schema: {ts_group.features_schema}")
                else:
                    lines.append(f"- Features Schema: Varying between series")

                lines.append("")
                lines.append("**Data Access Information:**")
                lines.append(
                    "- Data is either stored in the data sources listed above or comes from the pipeline outputs")
                lines.append(
                    "- Use the file paths from data sources, or run the needed pipelines, to get the actual data")
                lines.append("")

    return "\n".join(lines)
