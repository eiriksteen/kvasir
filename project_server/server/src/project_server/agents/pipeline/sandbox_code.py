from pathlib import Path
from typing import List, Optional

from project_server.agents.pipeline.output import PipelineImplementationSpec
from synesis_schemas.main_server import ModelEntityWithModelDef


def _create_input_object(
    bearer_token: str,
    spec: PipelineImplementationSpec,
    model_entities: Optional[List[ModelEntityWithModelDef]] = None
) -> str:

    model_inputs_def = ""
    if model_entities:
        for model_entity in model_entities:
            config = model_entity.config
            config["weights_save_dir"] = Path(config["weights_save_dir"])
            config_str = repr(config).replace("PosixPath", "Path")
            model_entity_in_pipeline = next(
                m for m in spec.input_model_entities if m.model_entity_id == model_entity.id)
            model_inputs_def += f"    {model_entity_in_pipeline.code_variable_name} = {model_entity.model.python_class_name}(model_config=ModelConfig(**{config_str})),\n"

    code = (
        "from project_server.entity_manager import LocalDatasetManager\n\n" +
        f"dataset_manager = LocalDatasetManager('{bearer_token}')\n\n" +
        f"input_obj = {spec.input_dataclass_name}(\n" + model_inputs_def +
        "\n".join([f"    {input_group.code_variable_name} = (await dataset_manager.get_data_group_with_raw_data('{input_group.object_group_id}')).data," for input_group in spec.input_object_groups]) +
        f"\n function_args={spec.args_dataclass_name}())"
    )

    return code


def create_test_code_from_spec(
        bearer_token: str,
        spec: PipelineImplementationSpec,
        model_entities: Optional[List[ModelEntityWithModelDef]] = None) -> str:
    input_obj_definition = _create_input_object(
        bearer_token, spec, model_entities)

    code = (
        "import asyncio\n" +
        "from pathlib import Path\n\n" +
        "async def run_test():\n" +
        "\n".join(f"    {line}" for line in input_obj_definition.split("\n")) + "\n\n" +
        f"    output_obj = {spec.python_function_name}(input_obj)\n" +
        "    print(output_obj)\n\n" +
        "asyncio.run(run_test())\n"
    )

    return code


def create_final_pipeline_script(
    pipeline_script: str,
    spec: PipelineImplementationSpec,
    model_entities: Optional[List[ModelEntityWithModelDef]] = None
) -> str:

    function_args_def = f"function_args={spec.args_dataclass_name}(**inputs['function_args'])"

    model_config_imports, model_inputs_def = "", ""
    if len(spec.input_model_entities) > 0:
        assert model_entities is not None, "Model entities are required if there are input model entities"
        assert len(spec.input_model_entities) == len(
            model_entities), "Number of input model entities and model entities must match"

        model_config_imports = "\n".join(
            f"from {me.model.module_path} import ModelConfig as ModelConfig{me.model.python_class_name}" for me in model_entities) + "\n"

        model_inputs_def = ", ".join(
            [f"{m_in_pipeline.code_variable_name}={me.model.python_class_name}(model_config=ModelConfig{me.model.python_class_name}(**inputs['{m_in_pipeline.code_variable_name}_config']))"
             for me, m_in_pipeline in zip(model_entities, spec.input_model_entities)])

    input_object_group_def = ", ".join(
        [f"{o_in_pipeline.code_variable_name}=inputs['{o_in_pipeline.code_variable_name}']" for o_in_pipeline in spec.input_object_groups])

    # TODO: Make less ugly, and handle mixing async and sync functions
    final_script = (
        f"{pipeline_script}\n\n" +
        f"from project_server.entity_manager import PipelineManager\n" +
        "from uuid import UUID\n" +
        "from typing import Dict\n" +
        f"{model_config_imports}" +
        "from synesis_schemas.main_server import ObjectGroupInPipelineCreate, ModelEntityInPipelineCreate, PipelineOutputObjectGroupDefinitionCreate\n\n" +
        f"input_object_groups = {repr(spec.input_object_groups)}\n" +
        f"input_model_entities = {repr(spec.input_model_entities)}\n" +
        f"output_object_group_definitions = {repr(spec.output_object_group_definitions)}\n\n" +
        "async def run_pipeline(dataset_name: str, dataset_description: str, bearer_token: str, pipeline_id: UUID, weights_save_dirs: Dict[UUID, str]):\n" +
        "    pipeline_manager = PipelineManager(bearer_token)\n" +
        "    inputs = await pipeline_manager.load_pipeline_inputs(pipeline_id, input_object_groups, input_model_entities, weights_save_dirs)\n" +
        f"    outputs = {spec.python_function_name}({spec.input_dataclass_name}({function_args_def}, {input_object_group_def}, {model_inputs_def}))\n" +
        "    out = await pipeline_manager.save_pipeline_dataset_output(pipeline_id, dataset_name, dataset_description, outputs, output_object_group_definitions)\n" +
        "    print(out)\n"
    )

    return final_script
