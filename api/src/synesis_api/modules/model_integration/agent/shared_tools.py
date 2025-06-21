import re
from pydantic_ai import RunContext, ModelRetry
from synesis_api.utils import (
    add_line_numbers_to_script,
    replace_lines_in_script,
    add_lines_to_script_at_line,
    delete_lines_from_script,
    run_pylint
)

from synesis_api.modules.model_integration.agent.input_structures import (
    TIME_SERIES_INPUT_STRUCTURE,
    BASE_CONFIG_DEFINITION_CODE
)
from synesis_api.modules.model_integration.agent.output_structures import (
    TIME_SERIES_CLASSIFICATION_OUTPUT_STRUCTURE,
    TIME_SERIES_FORECASTING_OUTPUT_STRUCTURE,
    TIME_SERIES_SEGMENTATION_OUTPUT_STRUCTURE
)
from synesis_api.modules.model_integration.agent.base_deps import BaseDeps


async def get_repo_info(ctx: RunContext[BaseDeps], github_url: str, reasoning: str) -> str:
    """
    Get repository information including size and description using GitHub API.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: Repository information as a formatted string.
    """

    print("CALLING GET REPO INFO TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"GitHub URL: {github_url}")
    print("@"*50)

    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://api.github.com/repos/{owner}/{repo}',
        headers=headers
    )

    if response.status_code != 200:
        raise ModelRetry(f"Failed to get repository info: {response.text}")

    data = response.json()

    return (
        f"Repository: {data['full_name']}\n"
        f"Description: {data['description']}\n"
        f"Language: {data['language']}\n"
    )


async def get_repo_structure(ctx: RunContext[BaseDeps], github_url: str, reasoning: str) -> str:
    """
    Get the directory structure of a GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: Directory structure as a formatted string.
    """

    print("CALLING GET REPO STRUCTURE TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"GitHub URL: {github_url}")
    print("@"*50)

    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1',
        headers=headers
    )

    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1',
            headers=headers
        )
        if response.status_code != 200:
            raise ModelRetry(
                f"Failed to get repository structure: {response.text}")

    data = response.json()
    tree = data['tree']

    # Build directory structure
    structure = []
    for item in tree:
        if not any(excluded in item['path'] for excluded in ['.git/', 'node_modules/', '__pycache__/']):
            structure.append(
                f"{'📁 ' if item['type'] == 'tree' else '📄 '}{item['path']}")

    return "\n".join(structure)


async def get_file_content(ctx: RunContext[BaseDeps], github_url: str, file_path: str, reasoning: str) -> str:
    """
    Get the content of a specific file from the GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.
        file_path: Path to the file within the repository.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: File content as a string.
    """

    print("CALLING GET FILE CONTENT TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"GitHub URL: {github_url}")
    print(f"File path: {file_path}")
    print("@"*50)

    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}',
        headers=headers
    )

    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://raw.githubusercontent.com/{owner}/{repo}/master/{file_path}',
            headers=headers
        )
        if response.status_code != 200:
            raise ModelRetry(f"Failed to get file content: {response.text}")

    return response.text


def write_script(ctx: RunContext[BaseDeps], script: str, reasoning: str) -> str:
    """
    Write the script solving the current task to a file. 
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        script: The script to write.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The script with line numbers.
    """
    ctx.deps.current_script = add_line_numbers_to_script(script)

    print("CALLING WRITE SCRIPT TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"Script: {ctx.deps.current_script}")
    print("@"*50)

    out = f"UPDATED SCRIPT: \n\n <begin_script>\n\n {ctx.deps.current_script}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(ctx.deps.current_script)
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def replace_script_lines(ctx: RunContext[BaseDeps], line_number_start: int, line_number_end: int, new_code: str, reasoning: str) -> str:
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
    if not ctx.deps.current_script:
        return "No script to modify"

    ctx.deps.current_script = replace_lines_in_script(
        ctx.deps.current_script,
        line_number_start,
        line_number_end,
        new_code,
        script_has_line_numbers=True
    )

    print("CALLING REPLACE SCRIPT LINES TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"Line number start: {line_number_start}")
    print(f"Line number end: {line_number_end}")
    print(f"New code: {new_code}")
    print(f"Current script: {ctx.deps.current_script}")
    print("@"*50)

    out = f"UPDATED SCRIPT: \n\n <begin_script>\n\n {ctx.deps.current_script}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(ctx.deps.current_script)
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def add_script_lines(ctx: RunContext[BaseDeps], new_code: str, start_line: int, reasoning: str) -> str:
    """
    Add lines to the current script at the given line number.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        new_code: The new code to add. Remember indents if adding lines inside functions or classes!
        start_line: The line number to add the lines at. This line number is inclusive.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:
        str: The updated script.
    """
    if not ctx.deps.current_script:
        return "No script to modify"

    ctx.deps.current_script = add_lines_to_script_at_line(
        ctx.deps.current_script,
        new_code,
        start_line,
        script_has_line_numbers=True
    )

    print("CALLING ADD SCRIPT LINES TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"New code: {new_code}")
    print(f"Start line: {start_line}")
    print(f"Current script: {ctx.deps.current_script}")
    print("@"*50)

    out = f"UPDATED SCRIPT: \n\n <begin_script>\n\n {ctx.deps.current_script}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(ctx.deps.current_script)
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def delete_script_lines(ctx: RunContext[BaseDeps], line_number_start: int, line_number_end: int, reasoning: str) -> str:
    """
    Delete lines from the current script at the given line numbers.
    The script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback.

    Args:
        ctx: The context.
        line_number_start: The start line number of the code to delete. This line number is inclusive.
        line_number_end: The end line number of the code to delete. This line number is inclusive.
        reasoning: The concise reasoning for why you are calling this tool.

    Returns:    
        str: The updated script.
    """
    if not ctx.deps.current_script:
        return "No script to modify"

    ctx.deps.current_script = delete_lines_from_script(
        ctx.deps.current_script,
        line_number_start,
        line_number_end,
        script_has_line_numbers=True
    )

    print("CALLING DELETE SCRIPT LINES TOOL")
    print(f"Reasoning: {reasoning}")
    print(f"Line number start: {line_number_start}")
    print(f"Line number end: {line_number_end}")
    print(f"Current script: {ctx.deps.current_script}")
    print("@"*50)

    out = f"UPDATED SCRIPT: \n\n <begin_script>\n\n {ctx.deps.current_script}\n\n <end_script>"

    if ctx.deps.run_pylint:
        linter_output = run_pylint(ctx.deps.current_script)
        out += f"\n\n LINTER OUTPUT: \n\n <begin_linter_output>\n\n {linter_output}\n\n <end_linter_output>"

    out += "\n\nThe script is not automatically run and validated, you must call the final_result tool to submit the script for validation and feedback."

    return out


def get_input_structure(modality: str) -> str:
    """
    Get the input structure for a given modality.

    Args:
        modality: The modality of the data. Options: time_series

    Returns:
        str: The input structure for the given modality.
    """
    print("CALLING GET INPUT STRUCTURE TOOL")
    print(f"Modality: {modality}")
    print("@"*50)

    if modality == "time_series":
        return TIME_SERIES_INPUT_STRUCTURE
    else:
        raise ModelRetry(f"Modality {modality} not (yet) supported")


def get_base_config_definition_code() -> str:
    """
    Get the base config definition code.
    """
    print("CALLING GET BASE CONFIG DEFINITION CODE TOOL")
    print("@"*50)

    return BASE_CONFIG_DEFINITION_CODE


def get_output_structure(modality: str, task_name: str) -> str:
    """
    Get the output structure for a given task.

    Args:
        modality: The modality of the data. Options: time_series
        task_name: The name of the task. Options: forecasting, classification, regression, segmentation, other

    Returns:
        str: The output structure for the given task.
    """
    print("CALLING GET OUTPUT STRUCTURE TOOL")
    print(f"Modality: {modality}")
    print(f"Task name: {task_name}")
    print("@"*50)

    if modality == "time_series":
        if task_name == "forecasting":
            return TIME_SERIES_FORECASTING_OUTPUT_STRUCTURE
        # if task_name == "classification":
        #     return TIME_SERIES_CLASSIFICATION_OUTPUT_STRUCTURE
        # elif task_name == "forecasting":
        #     return TIME_SERIES_FORECASTING_OUTPUT_STRUCTURE
        # elif task_name == "segmentation":
        #     return TIME_SERIES_SEGMENTATION_OUTPUT_STRUCTURE
        else:
            return f"Task {task_name} not (yet) supported for time series data, only forecasting is supported for now"
    else:
        raise ModelRetry(f"Modality {modality} not (yet) supported")
