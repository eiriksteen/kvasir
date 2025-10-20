from typing import Literal, Optional
from pydantic_ai import RunContext, ModelRetry

from project_server.utils.code_utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
)
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.runner_base import CodeForLog
from project_server.client import post_search_functions
from project_server.agents.swe.utils import save_script_with_version_handling
from project_server.entity_manager.script_manager import script_manager
from project_server.app_secrets import (
    MODELS_MODULE, MODELS_MODULE_TMP, FUNCTIONS_MODULE, FUNCTIONS_MODULE_TMP, PIPELINES_MODULE, PIPELINES_MODULE_TMP, DATA_INTEGRATION_MODULE, DATA_INTEGRATION_MODULE_TMP
)
from synesis_schemas.main_server import QueryRequest, SearchFunctionsRequest, script_type_literal


swe_script_type_literal = Literal["function",
                                  "model",
                                  "pipeline",
                                  "data_integration"]


def _check_imports_tmp(script) -> tuple[bool, Optional[str]]:

    if MODELS_MODULE in script and not MODELS_MODULE_TMP in script:
        return False, f"Found imports from {MODELS_MODULE} but not from {MODELS_MODULE_TMP}. We must use the temporary modules!"
    if FUNCTIONS_MODULE in script and not FUNCTIONS_MODULE_TMP in script:
        return False, f"Found imports from {FUNCTIONS_MODULE} but not from {FUNCTIONS_MODULE_TMP}. We must use the temporary modules"
    if PIPELINES_MODULE in script and not PIPELINES_MODULE_TMP in script:
        return False, f"Found imports from {PIPELINES_MODULE} but not from {PIPELINES_MODULE_TMP}. We must use the temporary modules"
    if DATA_INTEGRATION_MODULE in script and not DATA_INTEGRATION_MODULE_TMP in script:
        return False, f"Found imports from {DATA_INTEGRATION_MODULE} but not from {DATA_INTEGRATION_MODULE_TMP}. We must use the temporary modules"
    return True, None


async def write_script(ctx: RunContext[SWEAgentDeps], script: str, file_name: str, script_type: script_type_literal) -> str:
    """
    Write a new script to a file. 
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback. 

    Args:
        ctx: The context.
        script: The script to write.
        file_name: The name of the new file to write the script to.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:
        str: The script with line numbers.
    """

    if not file_name.endswith(".py"):
        raise ModelRetry(
            f"File name must end with .py. Got: {file_name}")

    is_valid, error_message = _check_imports_tmp(script)
    if not is_valid:
        raise ModelRetry(error_message)

    file_storage = save_script_with_version_handling(
        ctx, file_name, script, script_type)

    script_with_line_numbers = add_line_numbers_to_script(script)
    out = f"NEW SCRIPT: \n\n <begin_script file_name={file_storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += f"You can now import it in your code from the module path: {file_storage.module_path}"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."
    out += f"\n\n The current scripts are: {list(ctx.deps.current_scripts.keys())}"

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=script, filename=file_storage.filename))

    return out


async def load_function_script_from_search(ctx: RunContext[SWEAgentDeps], module_path: str) -> str:
    """
    Loads a function script for use. 
    This should only be called after searching for pre-existing functions that you want to use. 

    Args:
        ctx: The context.
        module_path: The module path of the function to load.

    Returns:
        str: The loaded script.

    Raises:
        ModelRetry: If the function with the given module path is not found.
    """

    fn_to_load = next(iter(
        fn for fn in ctx.deps.functions_injected if fn.implementation_script.module_path == module_path), None)

    if fn_to_load is None:
        raise ModelRetry(
            f"Function with module path {module_path} not found. The loadable functions are: {list(fn.implementation_script.module_path for fn in ctx.deps.functions_injected)}")

    with open(fn_to_load.implementation_script.path, "r") as f:
        script = f.read()

    storage = script_manager.save_script(
        fn_to_load.implementation_script.filename, script, "function", add_uuid=False, temporary=True)

    ctx.deps.current_scripts[storage.filename] = script
    ctx.deps.functions_loaded.append(fn_to_load)

    script_with_line_numbers = add_line_numbers_to_script(script)
    out = (
        f"LOADED FUNCTION SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
        f"You can now import it in your code from the module path: {storage.module_path}"
        f"The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."
        f"The current scripts are: {list(ctx.deps.current_scripts.keys())}"
    )

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=script, filename=storage.filename))

    return out


def read_script(ctx: RunContext[SWEAgentDeps], file_name: str) -> str:
    """
    Read a script from the current scripts.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {ctx.deps.current_scripts.keys()}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]
    script_with_line_numbers = add_line_numbers_to_script(script)
    out = f"READ SCRIPT: \n\n <begin_script file_name={file_name}>\n\n {script_with_line_numbers}\n\n <end_script>"

    return out


async def replace_script_lines(
    ctx: RunContext[SWEAgentDeps],
    file_name: str,
    script_type: script_type_literal,
    line_number_start: int,
    line_number_end: int,
    new_code: str
) -> str:
    """
    Replace lines in the current script with new code.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to modify. This line number is inclusive.
        line_number_end: The end line number of the code to modify. This line number is inclusive.
        new_code: The new code to replace the old code at the given line numbers. Remember indents if adding lines inside functions or classes!
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    is_valid, error_message = _check_imports_tmp(script)
    if not is_valid:
        raise ModelRetry(error_message)

    updated_script = replace_lines_in_script(
        script,
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=False
    )

    storage = save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.\n"
    out += "Note that the version number may have increased in case of updates. "

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=updated_script, filename=storage.filename))

    return out


async def add_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, new_code: str, start_line: int) -> str:
    """
    Add lines to the current script at the given line number.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        new_code: The new code to add. Remember indents if adding lines inside functions or classes!
        start_line: The line number to add the lines at. This line number is inclusive.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    is_valid, error_message = _check_imports_tmp(script)
    if not is_valid:
        raise ModelRetry(error_message)

    updated_script = add_lines_to_script_at_line(
        script,
        new_code,
        start_line,
        script_has_line_numbers=False
    )

    storage = save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    if ctx.deps.log_code:
        await ctx.deps.log_code(CodeForLog(
            code=updated_script, filename=storage.filename))

    return out


async def delete_script_lines(ctx: RunContext[SWEAgentDeps], file_name: str, script_type: script_type_literal, line_number_start: int, line_number_end: int) -> str:
    """
    Delete lines from the current script at the given line numbers.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to delete. This line number is inclusive.
        line_number_end: The end line number of the code to delete. This line number is inclusive.
        script_type: The script type, one of function, model, pipeline, or data_integration.

    Returns:    
        str: The updated script.
    """
    if file_name not in ctx.deps.current_scripts:
        raise ModelRetry(
            f"Script {file_name} does not exist. The available scripts are: {list(ctx.deps.current_scripts.keys())}. To create a new script, call the write_script tool.")

    script = ctx.deps.current_scripts[file_name]

    is_valid, error_message = _check_imports_tmp(script)
    if not is_valid:
        raise ModelRetry(error_message)

    updated_script = delete_lines_from_script(
        script,
        line_number_start,
        line_number_end,
        script_has_line_numbers=False
    )

    storage = save_script_with_version_handling(
        ctx,
        file_name,
        updated_script,
        script_type
    )

    script_with_line_numbers = add_line_numbers_to_script(updated_script)
    out = f"UPDATED SCRIPT: \n\n <begin_script file_name={storage.filename}>\n\n {script_with_line_numbers}\n\n <end_script>"
    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    if ctx.deps.log_code:
        await ctx.deps.log_code(
            CodeForLog(code=updated_script, filename=storage.filename))

    return out


async def search_existing_functions(ctx: RunContext[SWEAgentDeps], query: QueryRequest) -> str:
    results = await post_search_functions(ctx.deps.client, SearchFunctionsRequest(queries=[query]))

    functions_injected = [f for result in results for f in result.functions]
    ctx.deps.functions_injected.extend(functions_injected)
    function_descriptions = "\n---\n\n".join(
        [f.description_for_agent for result in results for f in result.functions])

    function_descriptions = function_descriptions.replace(
        FUNCTIONS_MODULE, FUNCTIONS_MODULE_TMP)

    return function_descriptions
