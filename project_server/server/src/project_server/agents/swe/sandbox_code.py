from typing import List, Dict, Any

from synesis_schemas.main_server import DataSource, Dataset, ModelEntity, FunctionOutputObjectGroupDefinitionCreate
from project_server.agents.entity_sandbox_code import (
    get_object_group_imports,
    get_object_group_definitions,
    get_data_source_imports,
    get_data_source_definitions,
    get_model_entity_imports,
    get_model_entity_definitions
)


def get_main_skeleton(
    data_sources: List[DataSource],
    datasets: List[Dataset],
    model_entities: List[ModelEntity],
) -> str:
    """"
    Example generated structure:
    ```
    import asyncio
    from project_server.entity_manager import LocalDatasetManager
    from project_server.entity_manager import DataSourceManager
    from project_server.script_storage.models import MyModel


    # Add your main pipeline function here


    async def main(bearer_token: str, input_args: dict):
        dataset_manager = LocalDatasetManager(bearer_token=bearer_token)
        dataset_a_object_group_a = await dataset_manager.get_object_group_data_by_name(...)

        data_source_manager = DataSourceManager(bearer_token=bearer_token)
        data_source_a = await data_source_manager.get_data_source(...)

        model = MyModel(config=ModelConfig(...))

        # TODO: Call the main pipeline function here
        # input_args = MyPipelineArgs(**input_args)
        # outputs = ...
    ```
    """
    imports = ["import asyncio"]
    if datasets:
        imports.append(get_object_group_imports())
    if data_sources:
        imports.append(get_data_source_imports())
    if model_entities:
        imports.append(get_model_entity_imports(model_entities))

    imports_section = "\n".join(imports)

    definitions = []
    if datasets:
        definitions.append(get_object_group_definitions(
            datasets, "bearer_token", num_tab_indents=1))
    if data_sources:
        definitions.append(get_data_source_definitions(
            data_sources, "bearer_token", num_tab_indents=1))
    if model_entities:
        definitions.append(get_model_entity_definitions(
            model_entities, num_tab_indents=1))

    definitions_section = "\n\n".join(definitions)

    skeleton = f"{imports_section}\n\n"
    skeleton += "# Add your main pipeline function here\n\n\n"
    skeleton += 'async def main(bearer_token: str, input_args: dict):\n'
    skeleton += f"{definitions_section}\n\n"
    skeleton += "    # TODO: Call the main function(s) here as in the example\n"
    skeleton += "    # TODO: Implement and run the pipeline\n"
    skeleton += "    # input_args = MyPipelineArgs(**input_args)\n"
    skeleton += "    # NB: The variable name must be 'outputs'\n"
    skeleton += "    outputs = ...\n"
    skeleton += "    # Do not add any code processing the outputs, it will be added automatically\n"
    skeleton += "    # Also do not return anything! Your job is done after defining the outputs variable\n"

    return skeleton


def add_entry_point(
    implementation_script: str,
    bearer_token: str,
    input_args: dict
) -> str:
    entry_point = f'\nif __name__ == "__main__":\n'
    entry_point += f'   from pathlib import Path\n'
    entry_point += f'   asyncio.run(main({repr(bearer_token)}, {repr(input_args).replace("PosixPath", "Path")}))\n'

    return implementation_script + entry_point


def add_object_group_validation_code_to_implementation(
    implementation_script: str,
    output_object_group_definitions: List[FunctionOutputObjectGroupDefinitionCreate]
) -> str:
    if not output_object_group_definitions:
        return implementation_script

    validation_import = "from synesis_data_interface.structures.validation import validate_object_group_structure\n"

    if validation_import.strip() not in implementation_script:
        implementation_script = validation_import + implementation_script

    validation_calls = []
    for output_def in output_object_group_definitions:
        validation_calls.append(
            f"    validate_object_group_structure(outputs.{output_def.name})"
        )

    validation_section = "\n    # Validate outputs\n" + \
        "\n".join(validation_calls) + "\n"

    lines = implementation_script.split('\n')
    main_func_start_idx = None
    main_func_end_idx = len(lines)

    for i, line in enumerate(lines):
        if line.strip().startswith('async def main('):
            main_func_start_idx = i
        elif line.strip().startswith('if __name__') and main_func_start_idx is not None:
            main_func_end_idx = i
            break

    lines.insert(main_func_end_idx, validation_section)
    implementation_script = '\n'.join(lines)

    return implementation_script


def add_submit_pipeline_result_code_to_implementation(
    implementation_script: str,
    output_object_group_definitions: List[FunctionOutputObjectGroupDefinitionCreate],
    output_variable_group_schema: Dict[str, Any]
) -> str:
    required_imports = [
        "from uuid import UUID",
        "from synesis_schemas.main_server import FunctionOutputObjectGroupDefinitionCreate",
        "from project_server.entity_manager import PipelineManager"
    ]

    for required_import in required_imports:
        if required_import not in implementation_script:
            implementation_script = required_import + "\n" + implementation_script

    output_defs_repr = repr(output_object_group_definitions)
    output_variable_group_schema_repr = repr(output_variable_group_schema)

    submit_function = (
        f"async def submit_results(pipeline_id: UUID, dataset_name: str, dataset_description: str, bearer_token: str, outputs):\n" +
        f"   pipeline_manager = PipelineManager(bearer_token=bearer_token)\n" +
        f"   result = await pipeline_manager.save_pipeline_dataset_output(\n" +
        f"       pipeline_id=pipeline_id,\n" +
        f"       dataset_name=dataset_name,\n" +
        f"       dataset_description=dataset_description,\n" +
        f"       outputs=outputs,\n" +
        f"       output_object_group_definitions={output_defs_repr},\n" +
        f"       output_variable_group_schema={output_variable_group_schema_repr}\n" +
        f"   )\n" +
        f"   print(result)\n"
    )

    lines = implementation_script.split('\n')
    main_func_start_idx = None
    main_func_end_idx = len(lines)

    for i, line in enumerate(lines):
        if line.strip().startswith('async def main('):
            main_func_start_idx = i
        elif main_func_start_idx is not None:
            if line and not line[0].isspace():
                main_func_end_idx = i
                break

    lines.insert(main_func_end_idx, submit_function)
    implementation_script = '\n'.join(lines)

    return implementation_script


def add_submit_results_call_to_main(
    implementation_script: str,
    pipeline_id: str,
    dataset_name: str,
    dataset_description: str,
    bearer_token: str,
    input_args: dict
) -> str:
    submit_call = f"    await submit_results(pipeline_id={repr(pipeline_id)}, dataset_name={repr(dataset_name)}, dataset_description={repr(dataset_description)}, bearer_token={repr(bearer_token)}, outputs=outputs)\n"

    lines = implementation_script.split('\n')
    main_func_start_idx = None
    main_func_end_idx = len(lines)

    for i, line in enumerate(lines):
        if line.strip().startswith('async def main('):
            main_func_start_idx = i
        elif main_func_start_idx is not None:
            if line and not line[0].isspace():
                main_func_end_idx = i
                break

    lines.insert(main_func_end_idx, submit_call)
    implementation_script = '\n'.join(lines)

    implementation_script = add_entry_point(
        implementation_script, bearer_token, input_args)

    return implementation_script
