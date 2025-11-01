from typing import Optional

from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineInputEntities,
    PipelineOutputEntities,
    PipelineImplementation,
)


def get_pipeline_description(
    pipeline_in_db: PipelineInDB,
    inputs: PipelineInputEntities,
    outputs: PipelineOutputEntities,
    implementation: Optional[PipelineImplementation]
) -> str:
    """
    Generate a comprehensive description of a pipeline for use in prompts or displays.

    Args:
        pipeline: Pipeline object with implementation details

    Returns:
        A formatted string description of the pipeline
    """
    description = f"Pipeline: {pipeline_in_db.name}\n"
    description += f"- ID: {pipeline_in_db.id}\n"
    description += f"- Created: {pipeline_in_db.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if pipeline_in_db.description:
        description += f"- Description: {pipeline_in_db.description}\n"

    # Input entities
    if inputs.data_source_ids:
        description += f"- Input Data Sources: {len(inputs.data_source_ids)} sources\n"
    if inputs.dataset_ids:
        description += f"- Input Datasets: {len(inputs.dataset_ids)} datasets\n"
    if inputs.model_entity_ids:
        description += f"- Input Model Entities: {len(inputs.model_entity_ids)} entities\n"
    if inputs.analysis_ids:
        description += f"- Input Analyses: {len(inputs.analysis_ids)} analyses\n"

    # Output entities
    if outputs.dataset_ids:
        description += f"- Output Datasets: {len(outputs.dataset_ids)} datasets\n"
    if outputs.model_entity_ids:
        description += f"- Output Model Entities: {len(outputs.model_entity_ids)} entities\n"

    # Implementation details
    if implementation:
        impl = implementation
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

        if impl.runs:
            latest_run = max(impl.runs, key=lambda r: r.start_time)
            description += f"- Latest Run Status: {latest_run.status}\n"
            description += f"- Latest Run Start: {latest_run.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if latest_run.end_time:
                description += f"- Latest Run End: {latest_run.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

    return description
