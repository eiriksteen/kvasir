from pydantic_ai import RunContext, ModelRetry


from kvasir_research.agents.v1.analysis.deps import AnalysisDeps


async def submit_analysis_results(ctx: RunContext[AnalysisDeps], summary: str) -> str:
    if ctx.deps.analysis is None:
        raise ModelRetry("Analysis object not initialized")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting analysis results", "tool_call")

    # if no code cells, model retry
    has_code_cells = any(
        cell.type == "code"
        for section in ctx.deps.analysis.sections
        for cell in section.cells
    )
    if not has_code_cells:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "You must submit code cells", "error")
        raise ModelRetry("You must submit code cells")

    # if any empty sections, model retry
    if any(len(s.cells) == 0 for s in ctx.deps.analysis.sections):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "You must submit at least one code cell in each section", "error")
        raise ModelRetry(
            "No empty sections! ")

    total_cells = sum(len(s.cells) for s in ctx.deps.analysis.sections)
    if total_cells == 0:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Empty analysis, nothing to submit", "error")
        raise ModelRetry("Empty analysis, nothing to submit")

    result = await ctx.deps.ontology.describe_analysis(ctx.deps.analysis)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitted analysis results ({total_cells} cells)", "result")

    return result
