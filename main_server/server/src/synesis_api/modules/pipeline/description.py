from typing import Optional, List

from synesis_schemas.main_server import (
    PipelineInDB,
    PipelineRunEntities,
    PipelineRun,
    PipelineImplementation,
)


def get_pipeline_description(
    pipeline_in_db: PipelineInDB,
    supported_inputs: PipelineRunEntities,
    runs: List[PipelineRun],
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

    # Supported inputs (what can be used)
    if supported_inputs.data_source_ids:
        description += f"- Supported Data Sources: {len(supported_inputs.data_source_ids)} sources\n"
    if supported_inputs.dataset_ids:
        description += f"- Supported Datasets: {len(supported_inputs.dataset_ids)} datasets\n"
    if supported_inputs.model_entity_ids:
        description += f"- Supported Model Entities: {len(supported_inputs.model_entity_ids)} entities\n"

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

    # Run history
    if runs:
        description += f"\nRuns: {len(runs)} total\n"
        latest_run = max(runs, key=lambda r: r.start_time)
        description += f"- Latest Run Status: {latest_run.status}\n"
        description += f"- Latest Run Start: {latest_run.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if latest_run.end_time:
            description += f"- Latest Run End: {latest_run.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Show inputs/outputs of latest run
        if latest_run.inputs.dataset_ids or latest_run.inputs.data_source_ids or latest_run.inputs.model_entity_ids:
            description += f"- Latest Run Inputs: {len(latest_run.inputs.dataset_ids)} datasets, {len(latest_run.inputs.data_source_ids)} data sources, {len(latest_run.inputs.model_entity_ids)} model entities\n"
        if latest_run.outputs.dataset_ids or latest_run.outputs.data_source_ids or latest_run.outputs.model_entity_ids:
            description += f"- Latest Run Outputs: {len(latest_run.outputs.dataset_ids)} datasets, {len(latest_run.outputs.data_source_ids)} data sources, {len(latest_run.outputs.model_entity_ids)} model entities\n"

    return description
