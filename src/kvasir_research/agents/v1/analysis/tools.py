from uuid import UUID
from typing import Literal, Dict, Tuple
from pydantic_ai import RunContext, ModelRetry, FunctionToolset


from kvasir_research.utils.code_utils import remove_print_statements_from_code
from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_research.agents.v1.analysis.utils import notebook_to_string


async def create_or_replace_cell(ctx: RunContext[AnalysisDeps], content: str, name: str, cell_type: Literal["code", "markdown"]) -> str:
    await ctx.deps.callbacks.log(ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] create_or_replace_cell called: name={name}, cell_type={cell_type}, content_length={len(content)} chars", "tool_call")

    if cell_type == "code":
        past_code = _extract_code_from_previous_cells(ctx.deps.notebook, name)
        past_code_no_prints = remove_print_statements_from_code(past_code)
        full_code = f"{past_code_no_prints}\n\n{content}"
        out, err = await ctx.deps.sandbox.run_python_code(
            full_code,
            truncate_output=True,
            timeout=ctx.deps.time_limit
        )

        await ctx.deps.callbacks.log(ctx.deps.run_id,
                                     f"Analysis Agent [{ctx.deps.run_name}] executed code cell: {name}, output_length={len(out)} chars", "result")

        if err:
            await ctx.deps.callbacks.log(ctx.deps.run_id,
                                         f"Analysis Agent [{ctx.deps.run_name}] error executing code cell: {name}, error={err}", "error")
            raise ModelRetry(f"Error executing code cell: {err}")

        ctx.deps.notebook[name] = (cell_type, content)
        ctx.deps.notebook[f"{name}_output"] = ("output", out)
    else:
        ctx.deps.notebook[name] = (cell_type, content)

    await ctx.deps.callbacks.log(ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] create_or_replace_cell completed: name={name}, total_cells={len(ctx.deps.notebook)}", "tool_call")

    result = notebook_to_string(
        ctx.deps.notebook, ctx.deps.run_id, ctx.deps.run_name)

    return result


async def delete_cell(ctx: RunContext[AnalysisDeps], cell_name: str) -> str:
    await ctx.deps.callbacks.log(ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] delete_cell called: cell_name={cell_name}", "tool_call")

    del ctx.deps.notebook[cell_name]

    result = notebook_to_string(
        ctx.deps.notebook, ctx.deps.run_id, ctx.deps.run_name)
    await ctx.deps.callbacks.log(ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] delete_cell completed: cell_name={cell_name}, remaining_cells={len(ctx.deps.notebook)}", "tool_call")

    return result


analysis_toolset = FunctionToolset(
    tools=[
        create_or_replace_cell,
        delete_cell
    ],
    max_retries=3
)


###


def _extract_code_from_previous_cells(notebook: Dict[str, Tuple[str, str]], cell_name) -> str:

    code_cells = []
    for cell_name_in_notebook, (cell_type, content) in notebook.items():
        if cell_name_in_notebook == cell_name:
            break
        elif cell_type == "code":
            code_cells.append(content)

    return "\n\n".join(code_cells)
