import uuid
import asyncio
from typing import List, Literal, Optional
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from project_server.worker import logger
from project_server.agents.extraction.deps import ExtractionDeps
from project_server.agents.extraction.helper_agent import (
    data_source_agent,
    dataset_agent,
    pipeline_agent,
    model_entity_agent,
    HelperDeps
)
from project_server.client import ProjectClient
from project_server.agents.shared_tools import read_code_files_tool
from project_server.client.requests.entity_graph import create_edges, remove_edges
from synesis_schemas.main_server import EdgesCreate


# data sources


class EntityToCreate(BaseModel):
    type: Literal["data_source", "dataset",
                  "analysis", "pipeline", "model_entity"]
    description: str
    data_file_paths: List[str] = []
    code_file_paths: List[str] = []
    entity_id: Optional[uuid.UUID] = None


ENTITY_TYPE_TO_AGENT = {
    "data_source": data_source_agent,
    "dataset": dataset_agent,
    # "analysis": analysis_agent,
    "pipeline": pipeline_agent,
    "model_entity": model_entity_agent
}


async def submit_entities_to_create(ctx: RunContext[ExtractionDeps], entities: List[EntityToCreate]) -> str:
    """Submit entities to create."""

    logger.info(f"Submitting entities to create: {entities}")
    coroutines = []

    for entity in entities:
        code_file_contents = []
        for code_file_path in entity.code_file_paths:
            code_file_content = await read_code_files_tool(ctx, [code_file_path])
            code_file_contents.append(code_file_content)

        code_file_contents_str = "\n\n".join(code_file_contents)
        data_file_paths_str = "\n\n".join(entity.data_file_paths)

        prompt = (
            f"The entity description is: {entity.description}. " +
            f"The code file contents are: {code_file_contents_str}. " +
            f"The data file paths are: {data_file_paths_str}. " +
            (f"The target entity ID is: {entity.entity_id}." if entity.entity_id else "")
        )

        agent = ENTITY_TYPE_TO_AGENT[entity.type]
        routine = agent.run(
            prompt,
            deps=HelperDeps(
                client=ctx.deps.client,
                bearer_token=ctx.deps.bearer_token,
                project=ctx.deps.project,
                container_name=ctx.deps.container_name
            )
        )
        coroutines.append(routine)

    logger.info("RUNNING ASYNCIO GATHER")
    results = await asyncio.gather(*coroutines)
    results_str = "\n\n".join([result.output for result in results])
    logger.info("ASYNCIO GATHER COMPLETED, OUTPUT:")
    logger.info(results_str)
    logger.info("ASYNCIO GATHER COMPLETED, OUTPUT END")
    return results_str


async def submit_entity_edges(ctx: RunContext[ExtractionDeps], edges: EdgesCreate) -> str:
    """Submit edges between entities in the graph."""
    try:
        logger.info(f"Submitting entity edges: {edges}")
        await create_edges(ctx.deps.client, edges)
        return "Successfully submitted entity edges to the system"
    except Exception as e:
        logger.error(f"Failed to submit entity edges to the system: {str(e)}")
        raise ModelRetry(
            f"Failed to submit entity edges to the system: {str(e)}")


async def remove_entity_edges(ctx: RunContext[ExtractionDeps], edges: EdgesCreate) -> str:
    """Remove edges between entities in the graph."""
    try:
        logger.info(f"Removing entity edges: {edges}")
        await remove_edges(ctx.deps.client, edges)
        return "Successfully removed entity edges from the system"
    except Exception as e:
        logger.error(
            f"Failed to remove entity edges from the system: {str(e)}")
        raise ModelRetry(
            f"Failed to remove entity edges from the system: {str(e)}")


# TODO: Add analyses


extraction_toolset = FunctionToolset(
    tools=[
        submit_entities_to_create,
        submit_entity_edges,
        remove_entity_edges
    ],
    max_retries=3
)
