from synesis_schemas.main_server import (
    FunctionWithoutEmbedding,
    FunctionDefinitionInDB,
)


# Description utilities

def get_function_description(
    function: FunctionWithoutEmbedding,
    definition: FunctionDefinitionInDB,
    implementation_script_path: str,
    # setup_script_path: Optional[str] = None
) -> str:
    """
    Generate a comprehensive description of a function for use in prompts or displays.

    Args:
        function: A Function instance

    Returns:
        A formatted string description of the function
    """
    lines = [
        f"## Function: {definition.name}",
        f"",
        f"**Function Definition ID:** `{definition.id}`",
        f"**Type:** {definition.type}",
        f"",
        f"**Implementation ID:** `{function.id}`",
        f"**Version:** v{function.version}",
        f"**Save Path:** `{implementation_script_path}`",
        f"**Python Function:** `{function.python_function_name}`",
        f"",
    ]

    if function.description:
        lines.append(f"{function.description}")
        lines.append("")

    if function.newest_update_description:
        lines.append(
            f"**Latest Update:** {function.newest_update_description}")
        lines.append("")

    if function.docstring:
        lines.append("**Documentation:**")
        lines.append("```")
        lines.append(f"{function.docstring}")
        lines.append("```")
        lines.append("")

    # Function signature
    lines.append("### Function Signature")
    lines.append("")
    lines.append(f"**Arguments:** `{function.args_schema}`")
    if function.default_args:
        lines.append(f"**Defaults:** `{function.default_args}`")
    lines.append(
        f"**Returns the variables:** `{function.output_variables_schema}`")
    lines.append("")

    return "\n".join(lines)
