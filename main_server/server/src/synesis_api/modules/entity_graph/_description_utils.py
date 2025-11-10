from typing import List
from uuid import UUID

from synesis_schemas.main_server import (
    DataSource,
    Dataset,
    Pipeline,
    ModelEntity,
    Analysis,
    EdgePoints,
    NotebookSection
)

# Type alias for entity map
EntityMap = dict[tuple[UUID, str],
                 DataSource | Dataset | Pipeline | ModelEntity | Analysis]


def get_data_source_description(data_source: DataSource, from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Generate comprehensive description for data source including inputs/outputs."""
    description = f"Data Source: {data_source.name}\n"
    description += f"- ID: {data_source.id}\n"
    description += f"- Type: {data_source.type}\n"
    description += f"- Created: {data_source.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if data_source.type_fields:
        type_fields = data_source.type_fields
        description += f"\nFile Information:\n"
        description += f"- File Name: {type_fields.file_name}\n"
        description += f"- File Path: {type_fields.file_path}\n"
        description += f"- File Type: {type_fields.file_type}\n"
        description += f"- File Size: {type_fields.file_size_bytes:,} bytes\n"

    if data_source.additional_variables:
        description += f"- Additional Variables: {data_source.additional_variables}\n"

    description += "\n" + \
        _get_edges_info(from_entities, to_entities, entity_map)
    return description


def get_dataset_description(dataset: Dataset, from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Generate comprehensive description for dataset including inputs/outputs."""
    lines = [
        f"## Dataset: {dataset.name} (ID: {dataset.id})",
        f"**Description:** {dataset.description}",
        f"**Created:** {dataset.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Updated:** {dataset.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if dataset.additional_variables:
        lines.append("### Dataset Additional Variables")
        for key, value in dataset.additional_variables.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    if dataset.object_groups:
        lines.append("### Object Groups")
        lines.append("")

        for object_group in dataset.object_groups:
            lines.append(f"#### {object_group.name} (ID: {object_group.id})")
            lines.append(f"**Type:** {object_group.modality}")
            lines.append(f"**Description:** {object_group.description}")
            lines.append(
                f"**Created:** {object_group.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            if object_group.additional_variables:
                lines.append("**Additional Variables:**")
                for key, value in object_group.additional_variables.items():
                    lines.append(f"- **{key}:** {value}")
                lines.append("")

            if object_group.modality == "time_series" and object_group.modality_fields:
                lines.append("**Time Series Group:**")
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
                        "- Sampling Frequency: Varying between series")
                if ts_group.timezone:
                    lines.append(f"- Timezone: {ts_group.timezone}")
                else:
                    lines.append("- Timezone: Varying between series")
                if ts_group.features_schema:
                    lines.append(
                        f"- Features Schema: {ts_group.features_schema}")
                else:
                    lines.append("- Features Schema: Varying between series")
                lines.append("")

    lines.append(_get_edges_info(from_entities, to_entities, entity_map))
    return "\n".join(lines)


def get_pipeline_description(pipeline: Pipeline, from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Generate comprehensive description for pipeline including inputs/outputs."""
    description = f"Pipeline: {pipeline.name}\n"
    description += f"- ID: {pipeline.id}\n"
    description += f"- Created: {pipeline.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if pipeline.description:
        description += f"- Description: {pipeline.description}\n"

    if pipeline.implementation:
        impl = pipeline.implementation
        description += f"\nImplementation Details:\n"
        description += f"- Function Name: {impl.python_function_name}\n"
        description += f"- Docstring: {impl.docstring}\n"

        if impl.description:
            description += f"- Implementation Description: {impl.description}\n"

        if impl.args_schema:
            description += f"- Arguments Schema: {impl.args_schema}\n"

        if impl.output_variables_schema:
            description += f"- Output Variables Schema: {impl.output_variables_schema}\n"

        if impl.functions:
            description += f"- Functions Used: {len(impl.functions)} functions\n"
            for func in impl.functions:
                description += f"  * {func.python_function_name}: {func.description}\n"

    if pipeline.runs:
        description += f"\nRuns: {len(pipeline.runs)} total\n"
        latest_run = max(pipeline.runs, key=lambda r: r.start_time)
        description += f"- Latest Run Status: {latest_run.status}\n"
        description += f"- Latest Run Start: {latest_run.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if latest_run.end_time:
            description += f"- Latest Run End: {latest_run.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

    description += "\n" + \
        _get_edges_info(from_entities, to_entities, entity_map)
    return description


def get_model_entity_description(model_entity: ModelEntity, from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Generate comprehensive description for model entity including inputs/outputs."""
    lines = [
        f"## Model Entity with name {model_entity.name} and ID: {model_entity.id}",
        "*(An instantiated and configured model entity)*",
        "",
        f"{model_entity.description}",
        "",
    ]

    if model_entity.implementation:
        model_entity_impl = model_entity.implementation
        lines.append(f"**Configuration:** {model_entity_impl.config}")
        lines.append(
            f"**Weights Directory:** {model_entity_impl.weights_save_dir or 'Not trained yet'}")
        lines.append("")

        model_impl = model_entity_impl.model_implementation
        lines.append(
            f"### Model Implementation with name `{model_impl.python_class_name}`, ID: {model_impl.id} and version (v{model_impl.version})")
        lines.append("*(An implemented version of the model definition)*")
        lines.append("")
        lines.append(
            f"**Module Path:** `{model_impl.implementation_script_path}`")
        lines.append(
            f"**Python Class Name:** `{model_impl.python_class_name}`")
        lines.append("")

        if model_impl.description:
            lines.append(f"{model_impl.description}")
            lines.append("")

        if model_impl.newest_update_description:
            lines.append(
                f"**Latest Update:** {model_impl.newest_update_description}")
            lines.append("")

        if model_impl.model_class_docstring:
            lines.append("**Class Documentation:**")
            lines.append("```")
            lines.append(f"{model_impl.model_class_docstring}")
            lines.append("```")
            lines.append("")

        definition = model_impl.definition
        lines.append(
            f"### Model Definition with name {definition.name} and ID: {definition.id}")
        lines.append(f"**Modality:** {definition.modality}")
        lines.append(f"**Task:** {definition.task}")
        lines.append("")

        training_function = model_impl.training_function
        lines.append("#### Training Function")
        lines.append("")
        if training_function.docstring:
            lines.append(f"{training_function.docstring}")
            lines.append("")
        lines.append(f"**Arguments:** `{training_function.args_schema}`")
        if training_function.default_args:
            lines.append(f"**Defaults:** `{training_function.default_args}`")
        lines.append(
            f"**Returns the variables:** `{training_function.output_variables_schema}`")
        lines.append("")

        inference_function = model_impl.inference_function
        lines.append("#### Inference Function")
        lines.append("")
        if inference_function.docstring:
            lines.append(f"{inference_function.docstring}")
            lines.append("")
        lines.append(f"**Arguments:** `{inference_function.args_schema}`")
        if inference_function.default_args:
            lines.append(f"**Defaults:** `{inference_function.default_args}`")
        lines.append(
            f"**Returns the variables:** `{inference_function.output_variables_schema}`")
        lines.append("")
    else:
        lines.append("*Note: No implementation selected yet*")
        lines.append("")

    lines.append(_get_edges_info(from_entities, to_entities, entity_map))
    return "\n".join(lines)


def get_analysis_description(analysis: Analysis, from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Generate comprehensive description for analysis including inputs/outputs."""
    lines = [
        f"The following is a textual representation of the analysis object with name {analysis.name} and id {analysis.id}:<<<",
        f"Analysis object: {analysis.name}",
        f"Analysis object description: {analysis.description}",
        "Each analysis object has an associated notebook structure with sections, subsections and analysis results.",
        "The following is a textual representation of the notebook:",
    ]

    if analysis.notebook:
        for section in analysis.notebook.notebook_sections:
            lines.extend(_get_section_description(section))

    lines.append(">>>")
    lines.append("")
    lines.append(_get_edges_info(from_entities, to_entities, entity_map))

    return "\n".join(lines)


def _get_section_description(section: NotebookSection) -> List[str]:
    """Helper to get section description recursively."""
    lines = []
    lines.append(f"Section: {section.section_name}")
    lines.append(f"Section id: {section.id}")
    if section.section_description:
        lines.append(f"Section description: {section.section_description}")
    if section.parent_section_id:
        lines.append(
            f"This section is a subsection of the section with id: {section.parent_section_id}")

    if len(section.analysis_results) > 0:
        lines.append(
            f"The following analysis results belong to the section with id {section.id}:")
    for i, analysis_result in enumerate(section.analysis_results):
        lines.append(f"Analysis result {i+1}: [")
        lines.append(f"Analysis result id: {analysis_result.id}")
        lines.append(f"Analysis result: {analysis_result.analysis}")
        lines.append(
            f"The result was from this code: {analysis_result.python_code}")
        lines.append("]")

    for subsection in section.notebook_sections:
        lines.extend(_get_section_description(subsection))

    return lines


def _get_edges_info(from_entities: EdgePoints, to_entities: EdgePoints, entity_map: EntityMap) -> str:
    """Format input/output edge information with entity details."""
    lines = ["### Inputs and Outputs", ""]

    # Inputs
    has_inputs = False
    input_lines = ["**Inputs:**"]

    if from_entities.data_sources:
        input_lines.append("- Data Sources:")
        for ds_id in from_entities.data_sources:
            entity = entity_map.get((ds_id, "data_source"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                input_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                input_lines.append(f"  * Unknown Data Source (ID: {ds_id})")
        has_inputs = True

    if from_entities.datasets:
        input_lines.append("- Datasets:")
        for dataset_id in from_entities.datasets:
            entity = entity_map.get((dataset_id, "dataset"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                input_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                input_lines.append(f"  * Unknown Dataset (ID: {dataset_id})")
        has_inputs = True

    if from_entities.pipelines:
        input_lines.append("- Pipelines:")
        for pipeline_id in from_entities.pipelines:
            entity = entity_map.get((pipeline_id, "pipeline"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                input_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                input_lines.append(f"  * Unknown Pipeline (ID: {pipeline_id})")
        has_inputs = True

    if from_entities.model_entities:
        input_lines.append("- Model Entities:")
        for me_id in from_entities.model_entities:
            entity = entity_map.get((me_id, "model_entity"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                input_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                input_lines.append(f"  * Unknown Model Entity (ID: {me_id})")
        has_inputs = True

    if from_entities.analyses:
        input_lines.append("- Analyses:")
        for analysis_id in from_entities.analyses:
            entity = entity_map.get((analysis_id, "analysis"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                input_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                input_lines.append(f"  * Unknown Analysis (ID: {analysis_id})")
        has_inputs = True

    if not has_inputs:
        input_lines.append("- None")

    lines.extend(input_lines)
    lines.append("")

    # Outputs
    has_outputs = False
    output_lines = ["**Outputs:**"]

    if to_entities.data_sources:
        output_lines.append("- Data Sources:")
        for ds_id in to_entities.data_sources:
            entity = entity_map.get((ds_id, "data_source"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                output_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                output_lines.append(f"  * Unknown Data Source (ID: {ds_id})")
        has_outputs = True

    if to_entities.datasets:
        output_lines.append("- Datasets:")
        for dataset_id in to_entities.datasets:
            entity = entity_map.get((dataset_id, "dataset"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                output_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                output_lines.append(f"  * Unknown Dataset (ID: {dataset_id})")
        has_outputs = True

    if to_entities.pipelines:
        output_lines.append("- Pipelines:")
        for pipeline_id in to_entities.pipelines:
            entity = entity_map.get((pipeline_id, "pipeline"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                output_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                output_lines.append(
                    f"  * Unknown Pipeline (ID: {pipeline_id})")
        has_outputs = True

    if to_entities.model_entities:
        output_lines.append("- Model Entities:")
        for me_id in to_entities.model_entities:
            entity = entity_map.get((me_id, "model_entity"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                output_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                output_lines.append(f"  * Unknown Model Entity (ID: {me_id})")
        has_outputs = True

    if to_entities.analyses:
        output_lines.append("- Analyses:")
        for analysis_id in to_entities.analyses:
            entity = entity_map.get((analysis_id, "analysis"))
            if entity:
                desc = f" - {entity.description}" if entity.description else ""
                output_lines.append(
                    f"  * {entity.name} (ID: {entity.id}){desc}")
            else:
                output_lines.append(
                    f"  * Unknown Analysis (ID: {analysis_id})")
        has_outputs = True

    if not has_outputs:
        output_lines.append("- None")

    lines.extend(output_lines)

    return "\n".join(lines)
