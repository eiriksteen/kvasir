import uuid
from typing import Literal, Optional, List
from pydantic import model_validator, BaseModel
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from synesis_schemas.main_server import (
    QueryRequest,
    ModelEntityImplementationCreate,
    ModelEntityInDB,
    AddEntityToProject,
    GetGuidelinesRequest,
    SearchModelsRequest,
    RunCreate,
    RunSpecificationCreate,
)
from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps
from synesis_api.modules.knowledge_bank.service import query_models, get_task_guidelines
from synesis_api.modules.model.service import create_model_entity_implementation
from synesis_api.modules.project.service import add_entity_to_project
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


class SWERunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    input_data_source_ids: List[uuid.UUID] = []
    input_dataset_ids: List[uuid.UUID]
    input_model_entity_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "SWERunDescriptionOutput":
        assert len(
            self.input_dataset_ids) + len(self.input_data_source_ids) > 0, "One or more dataset or data source IDs are required"
        return self


async def submit_run_for_analysis_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: AnalysisHandoffOutput
) -> str:
    """Submit a analysis agent run with the provided parameters."""

    # TODO: Implement

    return "Analysis agent run not yet implemented"


async def submit_run_for_swe_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: SWERunDescriptionOutput
) -> str:
    """Submit a SWE agent run with the provided parameters."""

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="swe",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            data_sources_in_run=result.input_data_source_ids,
            datasets_in_run=result.input_dataset_ids,
            model_entities_in_run=result.input_model_entity_ids,
            spec=RunSpecificationCreate(
                run_name=result.run_name,
                plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
                plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
                questions_for_user=result.questions_for_user,
                configuration_defaults_description=result.configuration_defaults_description)
        ))

    return f"Successfully submitted run for SWE agent, the run id is {run.id}"


async def search_existing_models(ctx: RunContext[OrchestratorAgentDeps], search_query: QueryRequest) -> str:
    if not search_query.query:
        raise ModelRetry("Query cannot be empty!")
    search_models_request = SearchModelsRequest(queries=[search_query])
    results = await query_models(ctx.deps.user_id, search_models_request)
    descriptions = "\n---\n\n".join(
        [m.description_for_agent for result in results for m in result.models])
    return descriptions


async def add_model_entity_to_project(ctx: RunContext[OrchestratorAgentDeps], model_entity_implementation_create: ModelEntityImplementationCreate) -> ModelEntityInDB:
    """
    Add an implemented model entity to the project. 
    You must provide the model_implementation_id and model_entity_create. 
    This should not be called before we have searched the models, as we need to know the model_implementation_id.
    """

    if not model_entity_implementation_create.model_implementation_id:
        raise ModelRetry("Model implementation ID is required!")

    if not model_entity_implementation_create.model_entity_create:
        raise ModelRetry("Model entity create is required!")

    try:
        new_model_entity = await create_model_entity_implementation(ctx.deps.user_id, model_entity_implementation_create)
    except Exception as e:
        raise ModelRetry(f"Error creating model entity implementation: {e}")

    await add_entity_to_project(ctx.deps.user_id, AddEntityToProject(
        project_id=ctx.deps.project_id,
        entity_type="model_entity",
        entity_id=new_model_entity.id
    ))

    return new_model_entity


def get_task_guidelines_tool(task: Literal["time_series_forecasting"]) -> str:
    return get_task_guidelines(GetGuidelinesRequest(task=task))
