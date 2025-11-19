from pydantic_ai import RunContext, ModelRetry

from kvasir_research.agents.v1.swe.deps import SWEDeps
from kvasir_research.agents.v1.swe.utils import modified_files_to_string


async def submit_implementation_results(ctx: RunContext[SWEDeps], execution_command: str) -> str:
    """
    Submit the execution command that runs your main script (which you should have created outside src/) and produces the output. 
    The execution_command should be a shell command (e.g., "python scripts/train_model.py --epochs 100" or "bash run_pipeline.sh").
    Remember to use any relevant evaluation code, if specified. 
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"SWE Agent [{ctx.deps.run_name}] submit_results called: execution_command={execution_command}", "tool_call")

    # If no execution command provided (e.g., only module modifications), skip execution
    if not execution_command or execution_command.strip() == "":
        result = modified_files_to_string(
            ctx.deps.modified_files, ctx.deps.run_id, ctx.deps.run_name, "", "")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                     f"SWE Agent [{ctx.deps.run_name}] submit_results completed (no execution): modified_files={list(ctx.deps.modified_files.keys())}", "result")
        return result

    # Execute the command via shell with streaming and timeout
    stdout_lines = []
    stderr_lines = []
    return_code = None
    timeout_message = None

    async for stream_type, content in ctx.deps.sandbox.run_shell_code_streaming(
        execution_command,
        timeout=ctx.deps.time_limit
    ):
        if stream_type == "returncode":
            return_code = content
        elif stream_type == "stdout":
            stdout_lines.append(content)
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"[{ctx.deps.run_name}] stdout: {content}", "result")
        elif stream_type == "stderr":
            stderr_lines.append(content)
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"[{ctx.deps.run_name}] stderr: {content}", "error")
        elif stream_type == "timeout":
            timeout_message = content
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"[{ctx.deps.run_id}] Timeout: {content}", "error")

    # Handle timeout
    if timeout_message:
        partial_out = "\n".join(stdout_lines)
        if partial_out:
            partial_out += "\n\n"

        error_msg = (
            f"{partial_out}"
            f"ERROR: Time limit exceeded ({ctx.deps.time_limit}s)\n"
            f"The execution was terminated because it exceeded the allocated time limit.\n"
            f"Consider optimizing the code, reducing the problem size, or using more efficient algorithms."
        )
        result = modified_files_to_string(
            ctx.deps.modified_files, ctx.deps.run_id, ctx.deps.run_name, execution_command, error_msg)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                     f"SWE Agent [{ctx.deps.run_name}] submit_results time limit exceeded: {ctx.deps.time_limit}s", "error")
        return result

    # Combine output
    out = "\n".join(stdout_lines)
    err = "\n".join(stderr_lines) if return_code != 0 else None

    if err:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                     f"SWE Agent [{ctx.deps.run_name}] submit_results error: execution_command={execution_command}, error={err}", "error")
        raise ModelRetry(f"Error running command '{execution_command}': {err}")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"SWE Agent [{ctx.deps.run_name}] submit_results completed: output_length={len(out)} chars, modified_files={list(ctx.deps.modified_files.keys())}", "result")

    result = modified_files_to_string(
        ctx.deps.modified_files, ctx.deps.run_id, ctx.deps.run_name, execution_command, out)

    return result


async def submit_message_to_orchestrator(ctx: RunContext[SWEDeps], message: str) -> str:
    """
    Submit a message to the orchestrator for help, to request an analysis, request access to write a file, or notify it of any critical issues. 
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"SWE Agent [{ctx.deps.run_name}] submit_message_to_orchestrator called: message={message}", "tool_call")
    result = modified_files_to_string(
        ctx.deps.modified_files, ctx.deps.run_id, ctx.deps.run_name, "", message)
    return result
