import uuid
import asyncio
from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, model_validator
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from project_server.worker import logger
from project_server.agents.extraction.deps import ExtractionDeps
from project_server.agents.extraction.helper_agent import (
    data_source_agent,
    dataset_agent,
    pipeline_agent,
    model_instantiated_agent,
    HelperDeps
)
from project_server.client import ProjectClient
from project_server.agents.shared_tools import read_code_files_tool
from project_server.client.requests.entity_graph import create_edges, remove_edges
from project_server.client.requests.data_sources import post_data_source
from project_server.client.requests.data_objects import post_dataset
from project_server.client.requests.pipeline import post_pipeline, post_pipeline_run
from project_server.client.requests.model import post_model_entity
from project_server.client.requests.project import post_add_entity
from synesis_schemas.main_server import (
    EdgesCreateUsingNames,
    EdgesCreate,
    EdgeDefinition,
    DataSourceCreate,
    DatasetCreate,
    PipelineCreate,
    PipelineRunCreate,
    ModelEntityCreate,
    AddEntityToProject,
    Project,
    DATA_SOURCE_TYPE_LITERAL
)


# data sources


class EntityToCreate(BaseModel):
    name: str
    type: Literal["data_source", "dataset", "analysis",
                  "pipeline", "model_instantiated"]
    description: str
    data_file_paths: List[str] = []
    code_file_paths: List[str] = []
    entity_id: Optional[uuid.UUID] = None
    data_source_type: Optional[DATA_SOURCE_TYPE_LITERAL] = None

    @model_validator(mode='after')
    def validate_data_source_type(self) -> 'EntityToCreate':
        if self.type == "data_source" and self.data_source_type is None:
            raise ValueError(
                "data_source_type must be specified when type is 'data_source'"
            )
        return self


class PipelineRunToCreate(BaseModel):
    name: str
    description: str
    pipeline_name: str


ENTITY_TYPE_TO_AGENT = {
    "data_source": data_source_agent,
    "dataset": dataset_agent,
    # "analysis": analysis_agent,
    "pipeline": pipeline_agent,
    "model_instantiated": model_instantiated_agent
}


def _find_entity_id_in_project_graph(
    project: Project,
    entity_name: str,
    entity_type: str
) -> Optional[uuid.UUID]:
    entity_list = []

    if entity_type == "data_source":
        entity_list = project.graph.data_sources
    elif entity_type == "dataset":
        entity_list = project.graph.datasets
    elif entity_type == "pipeline":
        entity_list = project.graph.pipelines
    elif entity_type == "analysis":
        entity_list = project.graph.analyses
    elif entity_type == "model_instantiated":
        entity_list = project.graph.model_instantiatedies
    elif entity_type == "pipeline_run":
        for pipeline in project.graph.pipelines:
            for run in pipeline.runs:
                if run.name == entity_name:
                    return run.id
        return None

    for entity in entity_list:
        if entity.name == entity_name:
            return entity.id

    return None


async def submit_entities_to_create(
    ctx: RunContext[ExtractionDeps],
    entities: List[EntityToCreate],
    pipeline_runs: List[PipelineRunToCreate],
    edges: List[EdgesCreateUsingNames]
) -> str:
    """Submit entities, pipeline runs, and edges to create."""

    logger.info(f"Submitting entities to create: {entities}")
    logger.info(f"Submitting pipeline runs to create: {pipeline_runs}")

    # Map entity names to IDs for edge creation
    name_to_id_map: Dict[str, uuid.UUID] = {}

    # Phase 1: Create empty base entities immediately for those without entity_id
    for entity in entities:
        if entity.entity_id is None:
            # Create new empty entity
            if entity.type == "data_source":
                # Create data source with details = None
                # data_source_type is guaranteed to be set by validator
                data_source_create = DataSourceCreate(
                    name=entity.name,
                    description=entity.description,
                    type=entity.data_source_type,
                    type_fields=None
                )
                result = await post_data_source(ctx.deps.client, data_source_create)
                name_to_id_map[entity.name] = result.id
                # Add to project
                await post_add_entity(ctx.deps.client, AddEntityToProject(
                    project_id=ctx.deps.project.id,
                    entity_type="data_source",
                    entity_id=result.id
                ))
                # Update entity_id for specialized agent
                entity.entity_id = result.id

                logger.info(
                    f"CTX DEPS LOG MESSAGE IS SET: {ctx.deps.log_message is not None}")
                if ctx.deps.log_message:
                    logger.info(f"CREATED DATA SOURCE")
                    await ctx.deps.log_message(f"CREATED DATA SOURCE", "result")

            elif entity.type == "dataset":
                # Create dataset with empty object groups
                dataset_create = DatasetCreate(
                    name=entity.name,
                    description=entity.description,
                    groups=[]
                )
                result = await post_dataset(ctx.deps.client, [], dataset_create)
                name_to_id_map[entity.name] = result.id
                # Add to project
                await post_add_entity(ctx.deps.client, AddEntityToProject(
                    project_id=ctx.deps.project.id,
                    entity_type="dataset",
                    entity_id=result.id
                ))
                # Update entity_id for specialized agent
                entity.entity_id = result.id

                if ctx.deps.log_message:
                    await ctx.deps.log_message(f"CREATED DATASET", "result")

            elif entity.type == "pipeline":
                # Create base pipeline entity
                pipeline_create = PipelineCreate(
                    name=entity.name,
                    description=entity.description
                )
                result = await post_pipeline(ctx.deps.client, pipeline_create)
                name_to_id_map[entity.name] = result.id
                # Add to project
                await post_add_entity(ctx.deps.client, AddEntityToProject(
                    project_id=ctx.deps.project.id,
                    entity_type="pipeline",
                    entity_id=result.id
                ))
                # Update entity_id for specialized agent
                entity.entity_id = result.id

                if ctx.deps.log_message:
                    await ctx.deps.log_message(f"CREATED PIPELINE", "result")

            elif entity.type == "model_instantiated":
                # Create base model entity
                model_instantiated_create = ModelEntityCreate(
                    name=entity.name,
                    description=entity.description
                )
                result = await post_model_entity(ctx.deps.client, model_instantiated_create)
                name_to_id_map[entity.name] = result.id
                # Add to project
                await post_add_entity(ctx.deps.client, AddEntityToProject(
                    project_id=ctx.deps.project.id,
                    entity_type="model_instantiated",
                    entity_id=result.id
                ))
                # Update entity_id for specialized agent
                entity.entity_id = result.id

                if ctx.deps.log_message:
                    await ctx.deps.log_message(f"CREATED MODEL ENTITY", "result")
        else:
            # Entity already exists, just add to map for edge creation
            name_to_id_map[entity.name] = entity.entity_id
            logger.info(
                f"Using existing entity: {entity.name} with ID: {entity.entity_id}")

    # Phase 1b: Create pipeline runs
    for pipeline_run in pipeline_runs:
        # Resolve pipeline name to ID from the name_to_id_map
        pipeline_id = name_to_id_map.get(pipeline_run.pipeline_name)
        if pipeline_id is None:
            logger.error(
                f"Pipeline run '{pipeline_run.name}' references pipeline '{pipeline_run.pipeline_name}' "
                f"which was not found in created entities. Available names: {list(name_to_id_map.keys())}"
            )
            continue

        pipeline_run_create = PipelineRunCreate(
            name=pipeline_run.name,
            description=pipeline_run.description,
            pipeline_id=pipeline_id,
            args={},
            output_variables={},
            status="completed"
        )
        result = await post_pipeline_run(ctx.deps.client, pipeline_run_create)
        name_to_id_map[pipeline_run.name] = result.id

    # Phase 2: Create edges
    logger.info(f"name_to_id_map contents: {name_to_id_map}")
    if edges:
        # Convert EdgesCreateUsingNames to EdgesCreate
        edge_definitions = []
        for edge in edges:
            for edge_def in edge.edges:
                # Try to get ID from newly created entities first
                from_id = name_to_id_map.get(edge_def.from_node_name)
                to_id = name_to_id_map.get(edge_def.to_node_name)

                # Fallback to looking up existing entities in the project graph
                if from_id is None:
                    from_id = _find_entity_id_in_project_graph(
                        ctx.deps.project,
                        edge_def.from_node_name,
                        edge_def.from_node_type
                    )
                    if from_id:
                        logger.info(
                            f"Found existing entity '{edge_def.from_node_name}' in project graph with ID: {from_id}")

                if to_id is None:
                    to_id = _find_entity_id_in_project_graph(
                        ctx.deps.project,
                        edge_def.to_node_name,
                        edge_def.to_node_type
                    )
                    if to_id:
                        logger.info(
                            f"Found existing entity '{edge_def.to_node_name}' in project graph with ID: {to_id}")

                if from_id is None or to_id is None:
                    logger.warning(
                        f"Could not find ID mapping for edge: {edge_def.from_node_name} -> {edge_def.to_node_name}")
                    logger.warning(
                        f"Available names in map: {list(name_to_id_map.keys())}")
                    logger.warning(f"from_id={from_id}, to_id={to_id}")
                    continue

                edge_definitions.append(EdgeDefinition(
                    from_node_type=edge_def.from_node_type,
                    from_node_id=from_id,
                    to_node_type=edge_def.to_node_type,
                    to_node_id=to_id
                ))

        if edge_definitions:
            edges_create = EdgesCreate(edges=edge_definitions)
            await create_edges(ctx.deps.client, edges_create)
            logger.info(f"Created {len(edge_definitions)} edges")

    if ctx.deps.initial_submission_callback:
        await ctx.deps.initial_submission_callback()

    # Phase 3: Call specialized agents to fill in details
    coroutines = []
    for entity in entities:
        assert entity.type in ENTITY_TYPE_TO_AGENT, f"No agent defined for entity type: {entity.type}"

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

    if coroutines:

        results = await asyncio.gather(*coroutines)
        results_str = "\n\n".join([result.output for result in results])
        return results_str
    else:
        logger.info("No specialized agents to run (no entities provided)")
        return "All entities and pipeline runs created successfully"


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
