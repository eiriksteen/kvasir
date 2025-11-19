import uuid
import asyncio
from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, model_validator
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from kvasir_research.agents.v1.deps import AgentDepsFull
from kvasir_research.agents.v1.extraction.deps import ExtractionDeps
from kvasir_research.agents.v1.extraction.helper_agent import (
    data_source_agent,
    dataset_agent,
    pipeline_agent,
    model_agent
)
from kvasir_research.agents.v1.shared_tools import read_files_tool
from kvasir_ontology.entities.data_source.data_model import DataSourceCreate, DATA_SOURCE_TYPE_LITERAL
from kvasir_ontology.entities.dataset.data_model import DatasetCreate
from kvasir_ontology.entities.pipeline.data_model import PipelineCreate, PipelineRunCreate
from kvasir_ontology.entities.model.data_model import ModelInstantiatedCreate
from kvasir_ontology.graph.data_model import EdgeDefinition, EdgeDefinitionUsingNames, EntityGraph


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


class EntitiesToUpdate(BaseModel):
    entity_id: uuid.UUID
    type: Literal["data_source", "dataset", "analysis",
                  "pipeline", "model_instantiated"]
    updates_to_make_description: str
    data_file_paths: List[str] = []
    code_file_paths: List[str] = []


class PipelineRunToCreate(BaseModel):
    name: str
    description: str
    pipeline_name: str


ENTITY_TYPE_TO_AGENT = {
    "data_source": data_source_agent,
    "dataset": dataset_agent,
    # "analysis": analysis_agent,
    "pipeline": pipeline_agent,
    "model_instantiated": model_agent
}


def _find_entity_id_in_project_graph(
    graph: EntityGraph,
    entity_name: str,
    entity_type: str
) -> Optional[uuid.UUID]:
    entity_list = []

    if entity_type == "data_source":
        entity_list = graph.data_sources
    elif entity_type == "dataset":
        entity_list = graph.datasets
    elif entity_type == "pipeline":
        entity_list = graph.pipelines
    elif entity_type == "analysis":
        entity_list = graph.analyses
    elif entity_type == "model_instantiated":
        entity_list = graph.models_instantiated
    elif entity_type == "pipeline_run":
        for pipeline in graph.pipelines:
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
    entities_to_create: List[EntityToCreate],
    pipeline_runs_to_create: List[PipelineRunToCreate],
    entities_to_update: List[EntitiesToUpdate],
    edges_to_create: List[EdgeDefinitionUsingNames]
) -> str:
    """Submit entities, pipeline runs, and edges to create."""

    await ctx.deps.callbacks.log(ctx.deps.run_id, f"Submitting entities to create: {entities_to_create}", "result")
    await ctx.deps.callbacks.log(ctx.deps.run_id, f"Submitting pipeline runs to create: {pipeline_runs_to_create}", "result")

    # Map entity names to IDs for edge creation
    name_to_id_map: Dict[str, uuid.UUID] = {}

    # Phase 1: Create empty base entities immediately for those without entity_id
    for entity in entities_to_create:
        if entity.entity_id is None:
            # Create new empty entity
            if entity.type == "data_source":
                data_source_create = DataSourceCreate(
                    name=entity.name,
                    description=entity.description,
                    type=entity.data_source_type,
                    type_fields=None
                )
                result = await ctx.deps.ontology.insert_data_source(data_source_create, [])
                name_to_id_map[entity.name] = result.id
                # Add to project
                # Update entity_id for specialized agent
                entity.entity_id = result.id
                await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"CREATED DATA SOURCE", "result")

            elif entity.type == "dataset":
                dataset_create = DatasetCreate(
                    name=entity.name,
                    description=entity.description,
                    groups=[]
                )
                result = await ctx.deps.ontology.insert_dataset(dataset_create, [])
                name_to_id_map[entity.name] = result.id
                # Add to project
                # Update entity_id for specialized agent
                entity.entity_id = result.id
                await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"CREATED DATASET", "result")

            elif entity.type == "pipeline":
                pipeline_create = PipelineCreate(
                    name=entity.name,
                    description=entity.description
                )
                result = await ctx.deps.ontology.insert_pipeline(pipeline_create, [])
                name_to_id_map[entity.name] = result.id
                # Add to project
                # Update entity_id for specialized agent
                entity.entity_id = result.id
                await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"CREATED PIPELINE", "result")

            elif entity.type == "model_instantiated":
                model_instantiated_create = ModelInstantiatedCreate(
                    name=entity.name,
                    description=entity.description
                )
                result = await ctx.deps.ontology.insert_model_instantiated(model_instantiated_create, [])
                name_to_id_map[entity.name] = result.id
                # Add to project
                # Update entity_id for specialized agent
                entity.entity_id = result.id
                await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"CREATED MODEL INSTANTIATED", "result")
        else:
            name_to_id_map[entity.name] = entity.entity_id
            await ctx.deps.callbacks.log(
                ctx.deps.run_id, f"Using existing entity: {entity.name} with ID: {entity.entity_id}", "result")

    # Phase 1b: Create pipeline runs
    for pipeline_run in pipeline_runs_to_create:
        # Resolve pipeline name to ID from the name_to_id_map
        pipeline_id = name_to_id_map.get(pipeline_run.pipeline_name)
        if pipeline_id is None:
            await ctx.deps.callbacks.log(
                ctx.deps.run_id, f"Pipeline run '{pipeline_run.name}' references pipeline '{pipeline_run.pipeline_name}' "
                f"which was not found in created entities. Available names: {list(name_to_id_map.keys())}", "error")
            continue

        pipeline_run_create = PipelineRunCreate(
            name=pipeline_run.name,
            description=pipeline_run.description,
            pipeline_id=pipeline_id,
            args={},
            output_variables={},
            status="completed"
        )
        result = await ctx.deps.ontology.pipelines.create_pipeline_run(pipeline_run_create)
        name_to_id_map[pipeline_run.name] = result.id

    # Phase 2: Create edges
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"name_to_id_map contents: {name_to_id_map}", "result")
    if edges_to_create:
        # Convert EdgesCreateUsingNames to EdgesCreate
        entity_graph = await ctx.deps.ontology.get_entity_graph()
        edge_definitions = []
        for edge in edges_to_create:
            # Try to get ID from newly created entities first
            from_id = name_to_id_map.get(edge.from_node_name)
            to_id = name_to_id_map.get(edge.to_node_name)

            # Fallback to looking up existing entities in the project graph
            if from_id is None:
                from_id = _find_entity_id_in_project_graph(
                    entity_graph,
                    edge.from_node_name,
                    edge.from_node_type
                )
                if from_id:
                    await ctx.deps.callbacks.log(
                        ctx.deps.user_id, ctx.deps.run_id, f"Found existing entity '{edge.from_node_name}' in project graph with ID: {from_id}", "result")

            if to_id is None:
                to_id = _find_entity_id_in_project_graph(
                    entity_graph,
                    edge.to_node_name,
                    edge.to_node_type
                )
                if to_id:
                    await ctx.deps.callbacks.log(
                        ctx.deps.user_id, ctx.deps.run_id, f"Found existing entity '{edge.to_node_name}' in project graph with ID: {to_id}", "result")

            if from_id is None or to_id is None:
                await ctx.deps.callbacks.log(
                    ctx.deps.user_id, ctx.deps.run_id, f"Could not find ID mapping for edge: {edge.from_node_name} -> {edge.to_node_name}", "error")
                await ctx.deps.callbacks.log(
                    ctx.deps.user_id, ctx.deps.run_id, f"Available names in map: {list(name_to_id_map.keys())}", "error")
                await ctx.deps.callbacks.log(ctx.deps.run_id, f"from_id={from_id}, to_id={to_id}", "error")
                continue

            edge_definitions.append(EdgeDefinition(
                from_node_type=edge.from_node_type,
                from_node_id=from_id,
                to_node_type=edge.to_node_type,
                to_node_id=to_id
            ))

        if edge_definitions:
            await ctx.deps.ontology.graph.create_edges(edge_definitions)
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created {len(edge_definitions)} edges", "result")

    # Phase 3: Call specialized agents to fill in details
    coroutines = []
    for entity in entities_to_create:
        assert entity.type in ENTITY_TYPE_TO_AGENT, f"No agent defined for entity type: {entity.type}"

        code_file_contents = []
        for code_file_path in entity.code_file_paths:
            code_file_content = await read_files_tool(ctx, [code_file_path])
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
            deps=AgentDepsFull(
                run_id=ctx.deps.run_id,
                callbacks=ctx.deps.callbacks,
                sandbox=ctx.deps.sandbox,
                sandbox_type=ctx.deps.sandbox_type,
                project_id=ctx.deps.project_id,
                package_name=ctx.deps.package_name,
                ontology=ctx.deps.ontology,
                bearer_token=ctx.deps.bearer_token
            )
        )
        coroutines.append(routine)

    for entity in entities_to_update:
        assert entity.type in ENTITY_TYPE_TO_AGENT, f"No agent defined for entity type: {entity.type}"
        agent = ENTITY_TYPE_TO_AGENT[entity.type]
        code_file_contents = []
        for code_file_path in entity.code_file_paths:
            code_file_content = await read_files_tool(ctx, [code_file_path])
            code_file_contents.append(code_file_content)

        code_file_contents_str = "\n\n".join(code_file_contents)
        data_file_paths_str = "\n\n".join(entity.data_file_paths)

        prompt = (
            f"You must add details to the entity with the following ID: {entity.entity_id}. " +
            f"A description of updates to make are: {entity.updates_to_make_description}. " +
            f"The code file contents are: {code_file_contents_str}. " +
            f"The data file paths are: {data_file_paths_str}. "
        )

        routine = agent.run(
            prompt,
            deps=AgentDepsFull(
                run_id=ctx.deps.run_id,
                callbacks=ctx.deps.callbacks,
                sandbox=ctx.deps.sandbox,
                sandbox_type=ctx.deps.sandbox_type,
                project_id=ctx.deps.project_id,
                package_name=ctx.deps.package_name,
                ontology=ctx.deps.ontology,
                bearer_token=ctx.deps.bearer_token
            )
        )
        coroutines.append(routine)

    if coroutines:
        results = await asyncio.gather(*coroutines)
        results_str = "\n\n".join([result.output for result in results])
        return results_str
    else:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "No specialized agents to run (no entities provided)", "error")
        return "All entities and pipeline runs created successfully"


async def submit_entity_edges(ctx: RunContext[ExtractionDeps], edges: List[EdgeDefinition]) -> str:
    """Submit edges between entities in the graph."""
    try:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting entity edges: {edges}", "result")
        await ctx.deps.ontology.graph.create_edges(edges)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Successfully submitted entity edges to the system", "result")
        return "Successfully submitted entity edges to the system"
    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Failed to submit entity edges to the system: {str(e)}", "error")
        raise ModelRetry(
            f"Failed to submit entity edges to the system: {str(e)}")


async def remove_entity_edges(ctx: RunContext[ExtractionDeps], edges: List[EdgeDefinition]) -> str:
    """Remove edges between entities in the graph."""
    try:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Removing entity edges: {edges}", "result")
        await ctx.deps.ontology.graph.remove_edges(edges)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Successfully removed entity edges from the system", "result")
        return "Successfully removed entity edges from the system"
    except Exception as e:
        await ctx.deps.callbacks.log(
            ctx.deps.user_id, ctx.deps.run_id, f"Failed to remove entity edges from the system: {str(e)}", "error")
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
