from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from kvasir_agents.utils.code_utils import is_readable_extension, add_line_numbers_to_script
from kvasir_agents.app_secrets import READABLE_EXTENSIONS
from kvasir_agents.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL, get_guidelines
from kvasir_agents.agents.v1.base_agent import AgentDeps


async def read_files_tool(ctx: RunContext[AgentDeps], file_paths: list[str]) -> str:
    f"""
    Read the contents of one or more text-based files.
    Only supports common text file formats: {', '.join(READABLE_EXTENSIONS)}

    Args:
        ctx: The run context.
        file_paths: List of file paths to read (relative to /app or absolute).

    Returns:
        The file contents, formatted with clear separators between files.
    """
    if not file_paths:
        raise ModelRetry("No file paths provided")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Reading {len(file_paths)} file(s): {', '.join(file_paths)}", "tool_call")

    results = []

    for file_path in file_paths:
        # Check if file has an allowed extension
        if not is_readable_extension(file_path):
            results.append(
                f"<begin_file file_path={file_path}>\n"
                f"ERROR: File does not have an allowed extension. Only text-based files are supported: {', '.join(sorted(READABLE_EXTENSIONS))}\n"
                f"<end_file>"
            )
            continue

        # Read file and check total line count
        shell_code = f"head -n 5000 {file_path} && wc -l < {file_path} || echo 'Error: File not found or cannot be read'"
        out, err = await ctx.deps.sandbox.run_shell_code(shell_code)

        if err or "Error:" in out or not out.strip():
            error_msg = err or out.strip()
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error reading file {file_path}: {error_msg}", "error")
            results.append(
                f"<begin_file file_path={file_path}>\n"
                f"ERROR: Could not read file - {error_msg}\n"
                f"<end_file>"
            )
            continue

        # Extract total line count from end of output
        total_lines = len(out.split('\n'))
        out_with_line_numbers = add_line_numbers_to_script(out)

        if total_lines > 5000:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Read file {file_path} (truncated: showing first 5000 of {total_lines} lines)", "result")
            results.append(
                f"<begin_file file_path={file_path}>\n\n{out_with_line_numbers}\n\n[TRUNCATED: Showing first 5000 of {total_lines} lines]\n\n<end_file>"
            )
        else:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Read file {file_path} ({total_lines} lines)", "result")
            results.append(
                f"<begin_file file_path={file_path}>\n\n{out_with_line_numbers}\n\n<end_file>"
            )

    separator = "\n\n" + "=" * 80 + "\n\n"
    result = separator.join(results)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Successfully read {len(file_paths)} file(s)", "result")
    return result


async def ls_tool(ctx: RunContext[AgentDeps], paths: list[str] = ["/app"]) -> str:
    if not paths:
        raise ModelRetry("No paths provided")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Listing directory contents: {', '.join(paths)}", "tool_call")

    results = []

    for directory_path in paths:
        shell_code = f"ls -I '__pycache__' -I '*.egg-info' {directory_path} || true"

        out, err = await ctx.deps.sandbox.run_shell_code(shell_code)

        if err:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error listing directory {directory_path}: {err}", "error")
            results.append(f"\n{directory_path}:\nError: {err}")
            continue

        if not out.strip():
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Directory {directory_path} is empty or does not exist", "result")
            results.append(f"\n{directory_path}:\n(empty or does not exist)")
        else:
            item_count = len(
                [item for item in out.strip().split('\n') if item.strip()])
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Listed {item_count} item(s) in {directory_path}", "result")
            if len(paths) > 1:
                results.append(f"\n{directory_path}:\n{out.rstrip()}")
            else:
                results.append(out.rstrip())

    separator = "\n" if len(paths) > 1 else ""
    result = separator.join(results).strip()
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Successfully listed contents of {len(paths)} directory/ies", "result")
    return result


navigation_toolset = FunctionToolset(
    tools=[
        read_files_tool,
        # ls is broken since it uses the internal cwd in modal and not the docker one
        # ls_tool
    ],
    max_retries=3
)


async def get_guidelines_tool(ctx: RunContext[AgentDeps], task: SUPPORTED_TASKS_LITERAL) -> str:
    """
    Get guidelines for a machine learning task.
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Getting guidelines for task: {task}", "tool_call")
    try:
        guidelines = get_guidelines(task)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Retrieved guidelines for {task} ({len(guidelines)} characters)", "result")
        return guidelines
    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error getting guidelines for {task}: {str(e)}", "error")
        raise ModelRetry(f"Error getting guidelines: {e}")


knowledge_bank_toolset = FunctionToolset(
    tools=[get_guidelines_tool],
    max_retries=3
)
