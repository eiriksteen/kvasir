from typing import List
from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition
from synesis_api.agents.model_integration.deps import ModelIntegrationDeps


async def filter_tools(ctx: RunContext[ModelIntegrationDeps],
                       tools: List[ToolDefinition]) -> List[ToolDefinition]:
    """
    Filter tools based on source and stage requirements.
    """
    filtered_tools = tools

    # Filter by source
    if ctx.deps.source == "pip":
        github_tools = ["get_repo_info",
                        "get_repo_structure",
                        "get_file_content"]
        filtered_tools = [
            tool_def for tool_def in filtered_tools if tool_def.name not in github_tools]

    # Filter by stage
    script_tools = ["replace_script_lines",
                    "add_script_lines",
                    "delete_script_lines",
                    "write_script"]

    if ctx.deps.stage == "implementation_planning":
        filtered_tools = [
            tool_def for tool_def in filtered_tools if tool_def.name not in script_tools]

    return filtered_tools
