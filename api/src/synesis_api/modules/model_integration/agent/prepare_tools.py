from typing import List
from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition


async def filter_tools_by_source(ctx: RunContext,
                                 tools: List[ToolDefinition]) -> List[ToolDefinition]:

    if ctx.deps.source == "pip":
        github_tools = ["get_repo_info",
                        "get_repo_structure",
                        "get_file_content"]

        return [tool_def for tool_def in tools if tool_def.name not in github_tools]

    return tools
