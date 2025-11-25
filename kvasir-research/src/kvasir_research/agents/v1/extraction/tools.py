import uuid
import asyncio
from typing import List, Literal, Optional
from pydantic import BaseModel, model_validator
from pydantic_ai import RunContext, ModelRetry, FunctionToolset, Agent

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
from kvasir_ontology.entities.model.data_model import ModelInstantiatedCreate, ModelCreate
from kvasir_ontology.graph.data_model import EdgeDefinition


# data sources


class EntityToCreate(BaseModel):
    name: str
    type: Literal["data_source", "dataset", "analysis", "pipeline"]
    description: str
    x_position: float
    y_position: float
    data_file_paths: List[str] = []
    code_file_paths: List[str] = []
    data_source_type: Optional[DATA_SOURCE_TYPE_LITERAL] = None

    @model_validator(mode='after')
    def validate_data_source_type(self) -> 'EntityToCreate':
        if self.type == "data_source" and self.data_source_type is None:
            raise ValueError(
                "data_source_type must be specified when type is 'data_source'"
            )
        return self


class ModelInstantiationToCreate(BaseModel):
    name: str
    description: str
    x_position: float
    y_position: float


class ModelToCreate(BaseModel):
    name: str
    description: str
    instantiations_to_create: List[ModelInstantiationToCreate]


class EntitiesToUpdate(BaseModel):
    entity_id: uuid.UUID
    type: Literal["data_source", "dataset", "pipeline", "model"]
    updates_to_make_description: str
    data_file_paths: List[str] = []
    code_file_paths: List[str] = []


ENTITY_TYPE_TO_AGENT = {
    "data_source": data_source_agent,
    "dataset": dataset_agent,
    # "analysis": analysis_agent,
    "pipeline": pipeline_agent,
    "model": model_agent
}


async def submit_entities_to_create_or_update(
    ctx: RunContext[ExtractionDeps],
    entities_to_create: List[EntityToCreate],
    entities_to_update: List[EntitiesToUpdate],
    models_to_create: List[ModelToCreate]
) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting submit_entities_to_create_or_update: {len(entities_to_create)} entity/ies to create, {len(entities_to_update)} to update, {len(models_to_create)} model(s) to create", "tool_call")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Entities to create: {entities_to_create}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Entities to update: {entities_to_update}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Models to create: {models_to_create}", "result")

    name_to_id_map = {}
    model_name_to_id_map = {}
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting entity creation phase: processing {len(entities_to_create)} entity/ies", "result")
    for i, entity in enumerate(entities_to_create, 1):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating entity {i}/{len(entities_to_create)}: {entity.name} (type: {entity.type})", "result")
        if entity.type == "data_source":
            data_source_create = DataSourceCreate(
                name=entity.name,
                description=entity.description,
                type=entity.data_source_type,
                type_fields=None
            )
            result = await ctx.deps.ontology.insert_data_source(data_source_create, [], entity.x_position, entity.y_position)
            name_to_id_map[entity.name] = result.id
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created data source: {entity.name}", "result")

        elif entity.type == "dataset":
            dataset_create = DatasetCreate(
                name=entity.name,
                description=entity.description,
                groups=[]
            )
            result = await ctx.deps.ontology.insert_dataset(dataset_create, [], entity.x_position, entity.y_position)
            name_to_id_map[entity.name] = result.id
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created dataset: {entity.name}", "result")

        elif entity.type == "pipeline":
            pipeline_create = PipelineCreate(
                name=entity.name,
                description=entity.description
            )
            result = await ctx.deps.ontology.insert_pipeline(pipeline_create, [], entity.x_position, entity.y_position)
            name_to_id_map[entity.name] = result.id
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created pipeline: {entity.name}", "result")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting model creation phase: processing {len(models_to_create)} model(s)", "result")
    for i, model_to_create in enumerate(models_to_create):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating model {i}/{len(models_to_create)}: {model_to_create.name} with {len(model_to_create.instantiations_to_create)} instantiation(s)", "result")

        model_create = ModelCreate(
            name=model_to_create.name, description=model_to_create.description)
        model_created = await ctx.deps.ontology.models.create_model(model_create)
        model_name_to_id_map[model_to_create.name] = model_created.id
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created model: {model_to_create.name} (ID: {model_created.id})", "result")

        if model_to_create.instantiations_to_create:
            for j, instantiation in enumerate(model_to_create.instantiations_to_create, 1):
                model_instantiated_create = ModelInstantiatedCreate(
                    name=instantiation.name,
                    description=instantiation.description,
                    config={},
                    model_id=model_created.id
                )
                result = await ctx.deps.ontology.insert_model_instantiated(model_instantiated_create, [], instantiation.x_position, instantiation.y_position)
                name_to_id_map[instantiation.name] = result.id
                await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created instantiation {j}/{len(model_to_create.instantiations_to_create)}: {instantiation.name} for model {model_to_create.name}", "result")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Completed model creation phase. Created {len(model_name_to_id_map)} model(s). Model name-to-ID mapping: {model_name_to_id_map}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Completed entity creation phase. Created {len(name_to_id_map)} entity/ies. Name-to-ID mapping: {name_to_id_map}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting coroutine preparation phase for entities to create: {len(entities_to_create)} entity/ies", "result")

    coroutines = []
    for i, entity in enumerate(entities_to_create, 1):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Preparing coroutine {i}/{len(entities_to_create)} for entity: {entity.name} (type: {entity.type})", "result")
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
            (f"The target entity ID is: {name_to_id_map[entity.name]}.")
        )

        agent: Agent = ENTITY_TYPE_TO_AGENT[entity.type]
        routine = agent.run(
            prompt,
            deps=ExtractionDeps(
                user_id=ctx.deps.user_id,
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
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Added coroutine for entity: {entity.name}", "result")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting coroutine preparation phase for entities to update: {len(entities_to_update)} entity/ies", "result")
    for i, entity in enumerate(entities_to_update, 1):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Preparing coroutine {i}/{len(entities_to_update)} for entity update: {entity.entity_id} (type: {entity.type})", "result")
        assert entity.type in ENTITY_TYPE_TO_AGENT, f"No agent defined for entity type: {entity.type}"
        agent: Agent = ENTITY_TYPE_TO_AGENT[entity.type]
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
            deps=ExtractionDeps(
                user_id=ctx.deps.user_id,
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
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Added coroutine for entity update: {entity.entity_id}", "result")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Completed coroutine preparation for entities to update. Total coroutines: {len(coroutines)}", "result")
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting coroutine preparation phase for models to create: {len(models_to_create)} model(s)", "result")

    for i, model_to_create in enumerate(models_to_create, 1):
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Preparing coroutine {i}/{len(models_to_create)} for model: {model_to_create.name}", "result")

        model_id = model_name_to_id_map[model_to_create.name]
        instantiation_ids = [name_to_id_map[inst.name]
                             for inst in model_to_create.instantiations_to_create if inst.name in name_to_id_map]

        instantiation_info = []
        for inst, inst_id in zip(model_to_create.instantiations_to_create, instantiation_ids):
            instantiation_info.append(f"{inst.name} (ID: {inst_id})")

        prompt = (
            f"The model name is: {model_to_create.name}. " +
            f"The model description is: {model_to_create.description}. " +
            f"The model ID is: {model_id}. " +
            f"The model has {len(model_to_create.instantiations_to_create)} instantiation(s) with IDs: {instantiation_ids}. " +
            f"Instantiation details: {', '.join(instantiation_info)}. " +
            f"You must submit the model implementation details (if not already submitted) and configure all {len(model_to_create.instantiations_to_create)} instantiation(s) with their specific configs, weights_save_dir, etc. " +
            f"Each instantiation in your output must have model_id set to {model_id}."
        )

        routine = model_agent.run(
            prompt,
            deps=ExtractionDeps(
                user_id=ctx.deps.user_id,
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
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Added coroutine for model: {model_to_create.name}", "result")

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Completed coroutine preparation for models. Total coroutines: {len(coroutines)}", "result")

    if coroutines:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Starting background processing: {len(coroutines)} coroutine(s) to execute", "result")
        background_tasks = [asyncio.create_task(coro) for coro in coroutines]
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created {len(background_tasks)} background task(s)", "result")

        async def monitor_background_tasks():
            results = await asyncio.gather(*background_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    await ctx.deps.callbacks.log(
                        ctx.deps.user_id,
                        ctx.deps.run_id,
                        f"Error in background agent task {i+1}: {str(result)}",
                        "error"
                    )

        asyncio.create_task(monitor_background_tasks())
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Started background task monitor", "result")
        current_entity_graph_description = await ctx.deps.ontology.describe_mount_group()
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Successfully completed submit_entities_to_create_or_update: entities created and background tasks started", "result")
        return f"Successfully created the entities. Next, submit pipeline runs (Phase 2) referencing the pipeline IDs from the entity graph below, then create edges (Phase 3) to connect all entities. The current entity graph is:\n\n{current_entity_graph_description}"
    else:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Successfully completed submit_entities_to_create_or_update. ", "result")
        return "All entities and pipeline runs created successfully"


async def submit_pipeline_runs_to_create(ctx: RunContext[ExtractionDeps], pipeline_runs: List[PipelineRunCreate]) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting {len(pipeline_runs)} pipeline run(s) to create", "tool_call")
    try:
        await ctx.deps.ontology.pipelines.create_pipeline_runs(pipeline_runs)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Successfully created {len(pipeline_runs)} pipeline run(s)", "result")
        current_entity_graph_description = await ctx.deps.ontology.describe_mount_group()
        return f"Successfully created the pipeline runs. Next, create edges (Phase 3) to connect all entities and pipeline runs together. The current entity graph is:\n\n{current_entity_graph_description}"
    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error creating pipeline runs: {str(e)}", "error")
        raise ModelRetry(
            f"Failed to submit pipeline runs to the system: {str(e)}")


async def submit_edges_to_create(ctx: RunContext[ExtractionDeps], edges: List[EdgeDefinition]) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting {len(edges)} entity edge(s)", "tool_call")
    try:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating edge(s): {edges}", "result")
        await ctx.deps.ontology.graph.create_edges(edges)
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Successfully created {len(edges)} edge(s)", "result")
        current_entity_graph_description = await ctx.deps.ontology.describe_mount_group()
        return f"Successfully created the entity edges. Inspect the graph and check whether you need to create more edges. The current entity graph is:\n\n{current_entity_graph_description}"
    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error creating edges: {str(e)}", "error")
        raise ModelRetry(
            f"Failed to submit entity edges to the system: {str(e)}")


# TODO: Add analyses


extraction_toolset = FunctionToolset(
    tools=[
        submit_entities_to_create_or_update,
        submit_pipeline_runs_to_create,
        submit_edges_to_create
    ],
    max_retries=3
)
