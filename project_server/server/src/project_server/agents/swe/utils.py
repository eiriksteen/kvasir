from typing import List
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.swe.deps import SWEAgentDeps
from synesis_schemas.main_server import script_type_literal
from project_server.entity_manager.script_manager import script_manager


def extract_injected_file_names(deps: SWEAgentDeps) -> List[str]:
    all_script_names = []
    for function in deps.functions_injected:
        all_script_names.append(function.implementation_script.filename)
    for model in deps.model_entities_injected:
        all_script_names.append(
            model.implementation.model_implementation.implementation_script.filename)
    return all_script_names


def _has_version_suffix(file_name: str) -> bool:
    suffix = file_name.split("_")[-1][:-3]
    # return true if the suffix is v1, v2 .., v100, etc
    return suffix.startswith("v") and suffix[1:].isdigit()


def save_script_with_version_handling(
        ctx: RunContext[SWEAgentDeps],
        file_name: str,
        script_content: str,
        script_type: script_type_literal
):

    # Determine if this is the first modification of an input script
    injected_script_names = extract_injected_file_names(ctx.deps)
    if file_name in injected_script_names and file_name not in ctx.deps.modified_scripts_old_to_new_name:
        if not _has_version_suffix(file_name):
            raise ModelRetry(
                f"File name {file_name} needs version suffix to be updated. ")

        increase_version_number = True
    else:
        increase_version_number = False

    is_new_script = file_name not in ctx.deps.current_scripts
    if is_new_script:
        if _has_version_suffix(file_name):
            raise ModelRetry(
                f"File name {file_name} is a new script but already has a version suffix. The v1 suffix will be added automatically, do not include it in the file name. If you are trying to edit an existing script, use its current filename as input. ")

        add_uuid, add_v1 = True, True
    else:
        add_uuid, add_v1 = False, False

    # Save the script with appropriate version handling
    storage = script_manager.save_script(
        file_name,
        script_content,
        script_type,
        temporary=True,
        add_uuid=add_uuid,
        increase_version_number=increase_version_number,
        add_v1=add_v1
    )

    # Update context dependencies when version number increases
    if increase_version_number:
        ctx.deps.modified_scripts_old_to_new_name[file_name] = storage.filename
        ctx.deps.current_scripts.pop(file_name)

    if is_new_script:
        ctx.deps.new_scripts.add(storage.filename)

    ctx.deps.current_scripts[storage.filename] = script_content

    return storage
