from typing import Dict

from project_server.utils.code_utils import extract_function_definitions, extract_dataclass_definition
from project_server.entity_manager import file_manager


def describe_function_scripts(input_scripts: Dict[str, str]) -> str:
    function_descriptions = []
    for script_name, script in input_scripts.items():
        function_definitions = extract_function_definitions(script)
        dataclass_definitions = extract_dataclass_definition(script)
        script_module = file_manager.get_function_script_module(
            script_name, 0, is_temporary=True)

        function_description = (
            f"Description of script {script_name} contents:\n\n" +
            f"Function definitions:\n\n" +
            f"\n\n".join(function_definitions) +
            f"\n\nDataclass definitions:\n\n" +
            f"\n\n".join(dataclass_definitions) +
            f"Import module (NB: You must remember to use the full module path when importing the script): {script_module}"
        )

        function_descriptions.append(function_description)

    return "\n\n".join(function_descriptions)
