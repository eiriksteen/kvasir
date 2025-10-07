import httpx
from pathlib import Path
from typing import List
from pydantic import BaseModel
# from bs4 import BeautifulSoup

from project_server.agents.model_integration.output import ModelDescription
from synesis_schemas.main_server import FunctionInputObjectGroupDefinitionCreate


class PypiSearchResult(BaseModel):
    name: str
    version: str
    description: str


async def search_pypi_package(package_name: str) -> PypiSearchResult:
    url = f"https://pypi.org/pypi/{package_name}/json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        response_json = response.json()
        return PypiSearchResult(
            name=response_json["info"]["name"],
            version=response_json["info"]["version"],
            description=response_json["info"]["description"]
        )


def verify_package_and_version_in_search_results(search_results: List[PypiSearchResult], package_name: str, version: str) -> bool:
    for result in search_results:
        if result.name == package_name and result.version == version:
            return True
    return False


def _create_training_input_object(
    variable_name: str,
    input_structures: List[FunctionInputObjectGroupDefinitionCreate],
) -> str:

    return (
        "from synesis_data_structures.time_series.synthetic import generate_synthetic_data\n\n" +
        f"{variable_name} = TrainingInput(\n " +
        "\n".join([f"{input_structure.name} = generate_synthetic_data('{input_structure.structure_id}')," for input_structure in input_structures]) +
        f"\n function_args=TrainingArgs())"
    )


def _create_inference_input_object(
    variable_name: str,
    input_structures: List[FunctionInputObjectGroupDefinitionCreate],
) -> str:
    return (
        "from synesis_data_structures.time_series.synthetic import generate_synthetic_data\n\n" +
        f"{variable_name} = InferenceInput(\n" +
        "\n".join([f"{input_structure.name} = generate_synthetic_data('{input_structure.structure_id}')," for input_structure in input_structures]) +
        f"\n function_args=InferenceArgs())"
    )


def create_model_test_code_from_spec(model_spec_output: ModelDescription, model_weights_dir: Path) -> str:
    training_input_obj_definition = _create_training_input_object(
        "training_input_obj",
        model_spec_output.training_function.input_object_groups,
    )
    inference_input_obj_definition = _create_inference_input_object(
        "inference_input_obj",
        model_spec_output.inference_function.input_object_groups,
    )
    return (
        f"model_config = ModelConfig()\n\n" +
        f"model_weights_dir = Path('{str(model_weights_dir)}')\n\n" +
        f"model_config.weights_save_dir = model_weights_dir\n\n" +
        f"model = {model_spec_output.python_class_name}(model_config)\n" +
        f"{training_input_obj_definition}\n\n" +
        f"{inference_input_obj_definition}\n\n" +
        f"training_output = model.run_training(training_input_obj)\n" +
        f"model.load_trained_model()\n" +
        f"inference_output = model.run_inference(inference_input_obj)\n"
    )
