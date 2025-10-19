import uuid
from typing import Literal, Optional, List
from pydantic import model_validator, BaseModel
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from synesis_schemas.main_server import (
    QueryRequest,
    ModelQueryResult,
    ModelEntityCreate,
    ModelEntityInDB,
    AddEntityToProject,
    FrontendNodeCreate,
    GetGuidelinesRequest,
    SearchModelsRequest,
    RunCreate,
    RunSpecificationCreate,
)
from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps
from synesis_api.modules.knowledge_bank.service import query_models, get_task_guidelines
from synesis_api.modules.model.service import create_model_entity
from synesis_api.modules.project.service import add_entity_to_project
from synesis_api.modules.node.service import create_node
from synesis_api.modules.runs.service import create_run


class AnalysisHandoffOutput(BaseModel):
    run_name: str
    deliverable_description: str
    dataset_ids: Optional[List[uuid.UUID]] = None
    data_source_ids: Optional[List[uuid.UUID]] = None

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "AnalysisHandoffOutput":
        if self.dataset_ids is None:
            assert self.data_source_ids is not None, "Data source IDs are required when dataset IDs are not provided"
        return self


class PipelineRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    input_dataset_ids: List[uuid.UUID]
    input_model_entity_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "PipelineRunDescriptionOutput":
        assert len(
            self.input_dataset_ids) > 0, "One or more dataset IDs are required"
        return self


class DataIntegrationRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    data_source_ids: List[uuid.UUID] = []
    # For input datasets
    dataset_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_data_source_ids(self) -> "DataIntegrationRunDescriptionOutput":
        assert len(
            self.data_source_ids) > 0 or len(self.dataset_ids) > 0, "One or more data source IDs or dataset IDs are required"
        return self


class ModelIntegrationRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None


async def submit_run_for_analysis_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: AnalysisHandoffOutput
) -> str:
    """Submit a analysis agent run with the provided parameters."""

    # TODO: Implement

    return "Analysis agent run not yet implemented"


async def submit_run_for_pipeline_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: PipelineRunDescriptionOutput
) -> str:
    """Submit a pipeline agent run with the provided parameters."""

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="pipeline",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            datasets_in_run=result.input_dataset_ids,
            model_entities_in_run=result.input_model_entity_ids,
            spec=RunSpecificationCreate(
                run_name=result.run_name,
                plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
                plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
                questions_for_user=result.questions_for_user,
                configuration_defaults_description=result.configuration_defaults_description)
        ))

    return f"Successfully submitted run for pipeline agent, the run id is {run.id}"


async def submit_run_for_data_integration_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: DataIntegrationRunDescriptionOutput
) -> str:
    """Submit a data integration agent run with the provided parameters."""

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="data_integration",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            data_sources_in_run=result.data_source_ids,
            datasets_in_run=result.dataset_ids,
            spec=RunSpecificationCreate(
                run_name=result.run_name,
                plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
                plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
                questions_for_user=result.questions_for_user)
        ))

    return f"Successfully submitted run for data integration agent, the run id is {run.id}"


async def submit_run_for_model_integration_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: ModelIntegrationRunDescriptionOutput
) -> str:
    """Submit a model integration agent run with the provided parameters."""

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="model_integration",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            spec=RunSpecificationCreate(
                run_name=result.run_name,
                plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
                plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
                questions_for_user=result.questions_for_user
            )
        )
    )

    return f"Successfully submitted run for model integration agent, the run id is {run.id}"


async def search_existing_models(ctx: RunContext[OrchestratorAgentDeps], search_query: QueryRequest) -> ModelQueryResult:
    if not search_query.query:
        raise ModelRetry("Query cannot be empty!")
    search_models_request = SearchModelsRequest(
        queries=[search_query],
        bare=True
    )
    results = await query_models(ctx.deps.user_id, search_models_request)
    return results[0]


async def add_model_entity_to_project(ctx: RunContext[OrchestratorAgentDeps], model_entity_create: ModelEntityCreate) -> ModelEntityInDB:
    try:
        new_model_entity = await create_model_entity(ctx.deps.user_id, model_entity_create)
    except Exception as e:
        raise ModelRetry(f"Error creating model entity: {e}")

    await add_entity_to_project(AddEntityToProject(
        project_id=ctx.deps.project_id,
        entity_type="model_entity",
        entity_id=new_model_entity.id
    ))
    await create_node(FrontendNodeCreate(
        project_id=ctx.deps.project_id,
        type="model_entity",
        model_entity_id=new_model_entity.id
    ))

    return new_model_entity


def get_task_guidelines_tool(task: Literal["time_series_forecasting"]) -> str:
    return get_task_guidelines(GetGuidelinesRequest(task=task))
