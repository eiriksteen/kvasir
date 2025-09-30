import uuid
from typing import List

from project_server.agents.pipeline.output import DetailedPipelineDescription


def create_final_pipeline_script(
    pipeline_spec: DetailedPipelineDescription,
    pipeline_script: str,
    input_dataset_ids: List[uuid.UUID]
) -> str:
    """
    - Fixed params: input_dataset_ids, input_mapping, output_mapping, pipeline_output, pipeline_id
    - Params to be injected: dataset_name, dataset_description, bearer_token, pipeline_id
    """

    input_object_group_args = ', '.join(
        [f'{m.pipeline_input_variable_name}=inputs["{m.pipeline_input_variable_name}"]'for m in pipeline_spec.input_mapping.from_dataset_object_groups])

    if pipeline_spec.input_mapping.from_model_entities:
        model_weights_args = ', '.join(
            [f'{m.pipeline_input_weights_dir_variable_name}=inputs["{m.pipeline_input_weights_dir_variable_name}"]'for m in pipeline_spec.input_mapping.from_model_entities])
    else:
        model_weights_args = ''

    # TODO: Make less ugly, and handle mixing async and sync functions
    final_script = (
        f"{pipeline_script}\n\n" +
        f"from project_server.entity_manager import PipelineManager\n\n" +
        "from uuid import UUID\n\n" +
        "from synesis_schemas.main_server import PipelineInputMapping, PipelineOutputMapping, ObjectGroupCreate, VariableGroupCreate, DatasetObjectGroupInputMapping, ModelEntityInputMapping, PipelineOutputObjectGroupMapping, PipelineOutputVariableGroupMapping, MetadataDataframe\n\n" +
        f"input_mapping = {repr(pipeline_spec.input_mapping)}\n\n" +
        f"output_mapping = {repr(pipeline_spec.output_mapping)}\n\n" +
        f"input_dataset_ids = {repr(input_dataset_ids)}\n\n" +
        "async def run_pipeline(dataset_name: str, dataset_description: str, bearer_token: str, pipeline_id: UUID):\n" +
        "    pipeline_manager = PipelineManager(bearer_token)\n" +
        "    inputs = await pipeline_manager.load_pipeline_inputs(input_dataset_ids, input_mapping)\n" +
        f"    outputs = {pipeline_spec.name}({pipeline_spec.input_dataclass_name}(function_args={pipeline_spec.args_dataclass_name}(), {input_object_group_args}, {model_weights_args}))\n" +
        "    out = await pipeline_manager.save_pipeline_outputs(pipeline_id, dataset_name, dataset_description, outputs, output_mapping)\n" +
        "    print(out)\n"
    )

    return final_script
