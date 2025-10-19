from typing import List

from project_server.agents.swe.deps import FunctionInjected, ModelInjected


def describe_available_scripts(functions: List[FunctionInjected], models: List[ModelInjected]) -> str:

    script_descriptions = []
    for function in functions:
        function_description = (
            f"Description of script {function.filename} contents:\n\n" +
            f"Function docstring:\n\n" +
            f"{function.docstring}\n\n" +
            f"Import module (NB: You must remember to use this entire module path when importing the script): {function.module_path}"
        )
        script_descriptions.append(function_description)

    for model in models:
        model_description = (
            f"Description of script {model.filename} contents:\n\n" +
            f"Model class docstring:\n\n" +
            f"{model.model_class_docstring}\n\n" +
            f"Training function docstring:\n\n" +
            f"{model.training_function_docstring}\n\n" +
            f"Inference function docstring:\n\n" +
            f"{model.inference_function_docstring}\n\n" +
            f"Import module (NB: You must remember to use this entire module path when importing the script): {model.module_path}"
        )
        script_descriptions.append(model_description)

    return "\n\n".join(script_descriptions)
