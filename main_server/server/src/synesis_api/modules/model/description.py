from typing import Optional

from synesis_schemas.main_server import (
    ModelEntityInDB,
    ModelImplementation,
    ModelImplementationInDB,
    ModelDefinitionInDB,
    ModelFunctionInDB,
    ModelEntityImplementation
)


def get_model_description(
    model_in_db: ModelImplementationInDB,
    definition: ModelDefinitionInDB,
    training_function: ModelFunctionInDB,
    inference_function: ModelFunctionInDB,
    implementation_script_path: str,
    setup_script_path: Optional[str] = None

) -> str:
    lines = []

    # Model Definition Layer
    lines.extend([
        f"### Model Definition with name {definition.name} and ID: {definition.id}",
        f"*(The overarching model definition)*",
        f"",
        f"**Modality:** {definition.modality}",
        f"**Task:** {definition.task}",
        f"",
    ])

    # Model Implementation Layer
    lines.extend([
        f"### Model Implementation with name `{model_in_db.python_class_name}`, ID: {model_in_db.id} and version (v{model_in_db.version})",
        f"*(An implemented version of the model definition)*",
        f"",
        f"**Module Path:** `{implementation_script_path}`",
        f"**Python Class Name:** `{model_in_db.python_class_name}`",
        f"",
    ])

    if model_in_db.description:
        lines.append(f"{model_in_db.description}")
        lines.append("")

    if model_in_db.newest_update_description:
        lines.append(
            f"**Latest Update:** {model_in_db.newest_update_description}")
        lines.append("")

    if model_in_db.model_class_docstring:
        lines.append("**Class Documentation:**")
        lines.append("```")
        lines.append(f"{model_in_db.model_class_docstring}")
        lines.append("```")
        lines.append("")

    # Training function
    lines.extend([
        "#### Training Function",
        "",
    ])

    if training_function.docstring:
        lines.append(f"{training_function.docstring}")
        lines.append("")

    lines.append(
        f"**Arguments:** `{training_function.args_schema}`")
    if training_function.default_args:
        lines.append(
            f"**Defaults:** `{training_function.default_args}`")
    lines.append(
        f"**Returns the variables:** `{training_function.output_variables_schema}`")
    lines.append("")

    # Inference function
    lines.extend([
        "#### Inference Function",
        "",
    ])

    if inference_function.docstring:
        lines.append(f"{inference_function.docstring}")
        lines.append("")

    lines.append(
        f"**Arguments:** `{inference_function.args_schema}`")
    if inference_function.default_args:
        lines.append(
            f"**Defaults:** `{inference_function.default_args}`")
    lines.append(
        f"**Returns the variables:** `{inference_function.output_variables_schema}`")
    lines.append("")

    return "\n".join(lines)


def get_model_entity_description(model_entity: ModelEntityInDB, model_entity_impl: ModelEntityImplementation) -> str:
    """
    Generate a comprehensive description of a model entity for use in prompts or displays.

    Args:
        model_entity: A ModelEntityInDB instance
        model_entity_impl: A ModelEntityImplementation instance with the model implementation

    Returns:
        A formatted string description of the model entity
    """
    # Model Entity Layer
    lines = [
        f"## Model Entity with name {model_entity.name} and ID: {model_entity.id}",
        f"*(An instantiated and configured model entity)*",
        f"",
        f"{model_entity.description}",
        f"",
        f"**Configuration:** {model_entity_impl.config}",
        f"**Weights Directory:** {model_entity_impl.weights_save_dir or 'Not trained yet'}",
        f"",
    ]

    # Add model implementation description
    model_impl = model_entity_impl.model_implementation
    model_description = get_model_description(
        model_impl,
        model_impl.definition,
        model_impl.training_function,
        model_impl.inference_function,
        model_impl.implementation_script_path,
        model_impl.setup_script_path
    )
    lines.append("")
    lines.append(model_description)

    return "\n".join(lines)
