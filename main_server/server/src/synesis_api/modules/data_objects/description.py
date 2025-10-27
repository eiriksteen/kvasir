from typing import List

from synesis_schemas.main_server import (
    DatasetInDB,
    ObjectGroup,
    VariableGroupInDB,
)

from synesis_data_interface.structures.base.definitions import FEATURE_INFORMATION_SECOND_LEVEL_ID, ENTITY_METADATA_SECOND_LEVEL_ID
from synesis_data_interface.structures.time_series.definitions import TIME_SERIES_DATA_SECOND_LEVEL_ID
from synesis_data_interface.structures.time_series_aggregation.definitions import TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID, TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID


def get_dataset_description(dataset_in_db: DatasetInDB,
                            object_groups: List[ObjectGroup],
                            variable_groups: List[VariableGroupInDB],
                            # sources: DatasetSources
                            ) -> str:

    lines = [
        f"## Dataset: {dataset_in_db.name} (ID: {dataset_in_db.id})",
        f"{dataset_in_db.description}",
        f"",
    ]

    if object_groups:
        lines.append("### Object Groups")
        lines.append("")

        for object_group in object_groups:
            lines.append(
                f"**{object_group.name}** (ID: {object_group.id}, Type: {object_group.structure_type})")
            if object_group.description:
                lines.append(f"{object_group.description}")

            if object_group.structure_type == "time_series":
                # Time series data
                lines.append(f"*{TIME_SERIES_DATA_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.time_series_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.time_series_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.time_series_df_head}")
                lines.append("")

                # Entity metadata
                lines.append(f"*{ENTITY_METADATA_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.entity_metadata_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.entity_metadata_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.entity_metadata_df_head}")
                lines.append("")

                # Feature information
                lines.append(f"*{FEATURE_INFORMATION_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.feature_information_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.feature_information_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.feature_information_df_head}")
                lines.append("")

            elif object_group.structure_type == "time_series_aggregation":
                # Aggregation outputs
                lines.append(
                    f"*{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.time_series_aggregation_outputs_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.time_series_aggregation_outputs_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.time_series_aggregation_outputs_df_head}")
                lines.append("")

                # Aggregation inputs
                lines.append(
                    f"*{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.time_series_aggregation_inputs_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.time_series_aggregation_inputs_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.time_series_aggregation_inputs_df_head}")
                lines.append("")

                # Entity metadata
                lines.append(f"*{ENTITY_METADATA_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.entity_metadata_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.entity_metadata_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.entity_metadata_df_head}")
                lines.append("")

                # Feature information
                lines.append(f"*{FEATURE_INFORMATION_SECOND_LEVEL_ID}:*")
                lines.append(
                    f"Save path: `{object_group.save_path}/{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet`")
                lines.append(f"```")
                lines.append(
                    f"{object_group.structure_fields.feature_information_df_schema}")
                lines.append(f"```")
                if object_group.structure_fields.feature_information_df_head:
                    lines.append("Sample data:")
                    lines.append(
                        f"{object_group.structure_fields.feature_information_df_head}")
                lines.append("")

    if variable_groups:
        lines.append("### Variable Groups")
        lines.append("")

        for variable_group in variable_groups:
            lines.append(
                f"**{variable_group.name}** (ID: {variable_group.id})")
            if variable_group.description:
                lines.append(f"{variable_group.description}")
            lines.append(f"Save path: `{variable_group.save_path}`")
            lines.append(f"Schema: `{variable_group.group_schema}`")
            lines.append("")

    return "\n".join(lines)
