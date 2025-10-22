from typing import List

from synesis_schemas.main_server import (
    FunctionWithoutEmbedding,
    FunctionDefinitionInDB,
    FunctionInputObjectGroupDefinitionInDB,
    FunctionOutputObjectGroupDefinitionInDB,
    ScriptInDB
)


# Description utilities

def get_function_description(
    function: FunctionWithoutEmbedding,
    definition: FunctionDefinitionInDB,
    input_object_groups: List[FunctionInputObjectGroupDefinitionInDB],
    output_object_groups: List[FunctionOutputObjectGroupDefinitionInDB],
    implementation_script: ScriptInDB,
    # setup_script: Optional[ScriptInDB] = None
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
        f"**Module Path:** `{implementation_script.module_path}`",
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

    # Input object groups
    if input_object_groups:
        lines.append("### Input Object Groups")
        lines.append("")
        for obj_group in input_object_groups:
            req_marker = "✓" if obj_group.required else "○"
            lines.append(
                f"- {req_marker} `{obj_group.name}` (ID: {obj_group.id}, Type: {obj_group.structure_id})")
            if obj_group.description:
                lines.append(f"  {obj_group.description}")
        lines.append("")

    # Output object groups
    if output_object_groups:
        lines.append("### Output Object Groups")
        lines.append("")
        for obj_group in output_object_groups:
            lines.append(
                f"- `{obj_group.name}` (ID: {obj_group.id}, Type: {obj_group.structure_id})")
            lines.append(
                f"  Entity ID name: `{obj_group.output_entity_id_name}`")
            if obj_group.description:
                lines.append(f"  {obj_group.description}")
        lines.append("")

    return "\n".join(lines)
