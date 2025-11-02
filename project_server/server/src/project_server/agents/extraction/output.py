from pydantic_ai import RunContext, ModelRetry

from project_server.agents.extraction.deps import ExtractionDeps


async def submit_final_extraction_output(ctx: RunContext[ExtractionDeps], summary: str) -> str:

    # for all dsetts created, check that all object groups have a raw data function implemented
    for dset in ctx.deps.created_datasets:
        for group in dset.object_groups:
            if group.id not in ctx.deps.object_groups_with_raw_data_fn:
                raise ModelRetry(
                    f"Object group {group.id} has no raw data function implemented")

    return summary
