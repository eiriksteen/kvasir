from pydantic_ai import RunContext, ModelRetry

from project_server.agents.extraction.deps import ExtractionDeps


async def submit_final_extraction_output(ctx: RunContext[ExtractionDeps], summary: str) -> str:

    # for all datasets created, check that all object groups have a chart created
    for dset in ctx.deps.created_datasets:
        for group in dset.object_groups:
            if group.id not in ctx.deps.object_groups_with_charts:
                raise ModelRetry(
                    f"Object group {group.id} has no chart visualization created. "
                    "Please use create_chart_for_object_group to create a chart for this group."
                )

    return summary
