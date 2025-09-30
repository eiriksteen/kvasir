from typing import List, Union


from project_server.agents.pipeline.output import DetailedFunctionDescription, DetailedPipelineDescription
from synesis_schemas.main_server import FunctionInputObjectGroupDefinitionCreate


def _create_input_object(spec: Union[DetailedFunctionDescription, DetailedPipelineDescription]) -> str:

    return (
        "from synesis_data_structures.time_series.synthetic import generate_synthetic_data\n\n" +
        f"input_obj = {spec.input_dataclass_name}(\n" +
        "\n".join([f"    {input_group.name} = generate_synthetic_data('{input_group.structure_id}')," for input_group in spec.input_object_groups]) +
        f"\n function_args={spec.args_dataclass_name}())"
    )


def create_test_code_from_fn_spec(spec: Union[DetailedFunctionDescription, DetailedPipelineDescription]) -> str:

    input_obj_definition = _create_input_object(spec)

    code = (
        f"{input_obj_definition}\n\n" +
        f"output_obj = {spec.name}(input_obj)\n"
    )

    return code
