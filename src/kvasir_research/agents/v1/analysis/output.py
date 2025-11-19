from pydantic_ai import RunContext, ModelRetry


from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_research.agents.v1.analysis.utils import notebook_to_string


async def submit_analysis_results(ctx: RunContext[AnalysisDeps], summary: str) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] submit_results called: summary={summary}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] submit_results called: notebook_cells={len(ctx.deps.notebook)}", "result")

    # if no code cells, model retry
    if not any(cell_type == "code" for cell_type, _ in ctx.deps.notebook.values()):
        raise ModelRetry("You must submit code cells")

    if not ctx.deps.notebook:
        raise ModelRetry("Empty notebook, nothing to submit")

    result = notebook_to_string(
        ctx.deps.notebook, ctx.deps.run_id, ctx.deps.run_name)

    await ctx.deps.callbacks.save_result(ctx.deps.user_id, ctx.deps.run_id, result, "analysis")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id,
                                 f"Analysis Agent [{ctx.deps.run_name}] submit_results completed: notebook_cells={len(ctx.deps.notebook)}, saved to Redis", "result")

    return result
