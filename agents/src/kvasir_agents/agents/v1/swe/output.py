from typing import Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry


from kvasir_agents.agents.v1.swe.deps import SWEDeps


class SweOutput(BaseModel):
    execution_command: Optional[str] = None
    terminal_output: Optional[str] = None
    message: str


async def submit_implementation_results(ctx: RunContext[SWEDeps], execution_command: str) -> SweOutput:
    """
    Submit the execution command that runs your main script (which you should have created outside src/) and produces the output. 
    The execution_command should be a shell command (e.g., "python scripts/train_model.py --epochs 100" or "bash run_pipeline.sh").
    Remember to use any relevant evaluation code, if specified. 
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting implementation results: {execution_command}", "tool_call")

    # If no execution command provided (e.g., only module modifications), skip execution
    if not execution_command or execution_command.strip() == "":
        result = _modified_files_to_string(ctx)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitted implementation results (no execution, {len(ctx.deps.modified_files)} file(s) modified)", "result")
        return SweOutput(execution_command=None, terminal_output=None, message=result)

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
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Execution output: {content}", "result")
        elif stream_type == "stderr":
            stderr_lines.append(content)
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Execution error: {content}", "error")
        elif stream_type == "timeout":
            timeout_message = content
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Execution timeout: {content}", "error")

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
        result = _modified_files_to_string(
            ctx, execution_command=execution_command, execution_output=error_msg)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Execution time limit exceeded ({ctx.deps.time_limit}s)", "error")
        return SweOutput(execution_command=execution_command, terminal_output=error_msg)

    # Combine output
    out = "\n".join(stdout_lines)
    err = "\n".join(stderr_lines) if return_code != 0 else None

    if err:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Execution error: {err}", "error")
        raise ModelRetry(f"Error running command '{execution_command}': {err}")

    result = _modified_files_to_string(
        ctx, execution_command=execution_command, execution_output=out)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitted implementation results (output: {len(out)} characters, {len(ctx.deps.modified_files)} file(s) modified)", "result")
    return SweOutput(execution_command=execution_command, terminal_output=out, message=result)


async def submit_message_to_orchestrator(ctx: RunContext[SWEDeps], message: str) -> str:
    """
    Submit a message to the orchestrator for help, to request an analysis, request access to write a file, or notify it of any critical issues. 
    """
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Sending message to orchestrator: {message[:100]}...", "tool_call")
    result = _modified_files_to_string(ctx, message=message)
    message = f"{message}\n\n{result}"
    return SweOutput(execution_command=None, terminal_output=None, message=message)


###


def _modified_files_to_string(
        ctx: RunContext[SWEDeps],
        execution_command: Optional[str] = None,
        execution_output: Optional[str] = None,
        message: Optional[str] = None) -> str:
    result = [
        f'<swe_result pipeline_id="{ctx.deps.pipeline_id}" run_id="{ctx.deps.run_id}" run_name="{ctx.deps.run_name}">']

    if not ctx.deps.modified_files:
        result.append("")
        result.append("  (no files modified)")
    else:
        for file_path, content in ctx.deps.modified_files.items():
            result.append("")
            result.append(f'  <file path="{file_path}">')
            # Indent content lines
            for line in content.split("\n"):
                result.append(f"    {line}")
            result.append("  </file>")

    # Add execution command if provided
    if execution_command:
        result.append("")
        result.append(
            f'  <execution_command>{execution_command}</execution_command>')

    # Add execution output
    if execution_output:
        result.append("")
        result.append("  <execution_output>")
        for line in execution_output.split("\n"):
            result.append(f"    {line}")
        result.append("  </execution_output>")

    if message:
        result.append("")
        result.append("  <message>")
        for line in message.split("\n"):
            result.append(f"    {line}")
        result.append("  </message>")

    result.append("")
    result.append("</swe_result>")

    return "\n".join(result)
