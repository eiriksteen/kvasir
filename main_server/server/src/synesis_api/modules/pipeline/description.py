from typing import Optional

from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineImplementationInDB,
    Pipeline,
)


def get_pipeline_description(pipeline: Pipeline) -> str:
    """
    Generate a comprehensive description of a pipeline for use in prompts or displays.

    Args:
        pipeline: Pipeline object with implementation details

    Returns:
        A formatted string description of the pipeline
    """
    description = f"Pipeline: {pipeline.name}\n"
    description += f"- ID: {pipeline.id}\n"
    description += f"- Created: {pipeline.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if pipeline.description:
        description += f"- Description: {pipeline.description}\n"

    # Input entities
    if pipeline.inputs.data_source_ids:
        description += f"- Input Data Sources: {len(pipeline.inputs.data_source_ids)} sources\n"
    if pipeline.inputs.dataset_ids:
        description += f"- Input Datasets: {len(pipeline.inputs.dataset_ids)} datasets\n"
    if pipeline.inputs.model_entity_ids:
        description += f"- Input Model Entities: {len(pipeline.inputs.model_entity_ids)} entities\n"
    if pipeline.inputs.analysis_ids:
        description += f"- Input Analyses: {len(pipeline.inputs.analysis_ids)} analyses\n"

    # Output entities
    if pipeline.outputs.dataset_ids:
        description += f"- Output Datasets: {len(pipeline.outputs.dataset_ids)} datasets\n"
    if pipeline.outputs.model_entity_ids:
        description += f"- Output Model Entities: {len(pipeline.outputs.model_entity_ids)} entities\n"

    # Implementation details
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
                description += f"  * {func.name}: {func.description}\n"

        if impl.runs:
            latest_run = max(impl.runs, key=lambda r: r.start_time)
            description += f"- Latest Run Status: {latest_run.status}\n"
            description += f"- Latest Run Start: {latest_run.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if latest_run.end_time:
                description += f"- Latest Run End: {latest_run.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

    return description
