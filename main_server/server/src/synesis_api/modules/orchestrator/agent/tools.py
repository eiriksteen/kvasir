import uuid
from typing import Optional, List, Union
from pydantic import model_validator, BaseModel
from pydantic_ai import RunContext

from synesis_schemas.main_server import RunCreate
from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps
from synesis_api.modules.runs.service import create_run
from synesis_api.modules.entity_graph.service import get_entity_details


class AnalysisRunSubmission(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    input_data_source_ids: List[uuid.UUID] = []
    input_dataset_ids: List[uuid.UUID] = []
    input_model_entity_ids: List[uuid.UUID] = []
    input_analysis_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_input_ids(self) -> "AnalysisRunSubmission":
        assert len(
            self.input_dataset_ids) + len(self.input_data_source_ids) > 0, "One or more dataset or data source IDs are required"
        return self


class AnalysisRunSubmissionWithEntityId(AnalysisRunSubmission):
    analysis_entity_id: uuid.UUID


class SWERunSubmission(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    input_data_source_ids: List[uuid.UUID] = []
    input_dataset_ids: List[uuid.UUID] = []
    input_model_entity_ids: List[uuid.UUID] = []
    input_analysis_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "SWERunSubmission":
        assert len(
            self.input_dataset_ids) + len(self.input_data_source_ids) > 0, "One or more dataset or data source IDs are required"
        return self


class SWERunSubmissionWithEntityId(SWERunSubmission):
    pipeline_entity_id: uuid.UUID


async def submit_run_for_analysis_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: Union[AnalysisRunSubmission,
                  AnalysisRunSubmissionWithEntityId]
) -> str:
    """
    Submit a analysis agent run with the provided parameters. 
    The analysis_entity_id is the id of the entity to associate the run with. 
    For example, if there is an empty analysis entity with the name "EDA" and the user requests an EDA, this is the natural entity. 
    However, if there is no pre-existing entity to naturally associate with, this should be "null" and you must include the analysis_create object instead. 
    """

    if isinstance(result, AnalysisRunSubmissionWithEntityId):
        analysis_entity_id = result.analysis_entity_id
    else:
        analysis_entity_id = None

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="analysis",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            data_sources_in_run=result.input_data_source_ids,
            datasets_in_run=result.input_dataset_ids,
            model_entities_in_run=result.input_model_entity_ids,
            analyses_in_run=result.input_analysis_ids,
            run_name=result.run_name,
            plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
            plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
            target_entity_id=analysis_entity_id,

        ))

    return f"Successfully submitted run for SWE agent, the run id is {run.id}"


async def submit_run_for_swe_agent(
    ctx: RunContext[OrchestratorAgentDeps],
    result: Union[SWERunSubmission,
                  SWERunSubmissionWithEntityId]
) -> str:
    """Submit a SWE agent run with the provided parameters.
    The pipeline_entity_id is the id of the pipeline entity to associate the run with. 
    For example, if there is an empty pipeline entity with the name "Training Pipeline" and the user requests that training pipeline, this is the natural entity. 
    However, if there is no pre-existing entity to naturally associate with, this should be "null" and you must include the pipeline_create object instead. 
    """

    if isinstance(result, SWERunSubmissionWithEntityId):
        pipeline_entity_id = result.pipeline_entity_id
    else:
        pipeline_entity_id = None

    run = await create_run(
        ctx.deps.user_id,
        RunCreate(
            type="swe",
            project_id=ctx.deps.project_id,
            conversation_id=ctx.deps.conversation_id,
            data_sources_in_run=result.input_data_source_ids,
            datasets_in_run=result.input_dataset_ids,
            model_entities_in_run=result.input_model_entity_ids,
            analyses_in_run=result.input_analysis_ids,
            run_name=result.run_name,
            plan_and_deliverable_description_for_agent=result.plan_and_deliverable_description_for_agent,
            plan_and_deliverable_description_for_user=result.plan_and_deliverable_description_for_user,
            questions_for_user=result.questions_for_user,
            configuration_defaults_description=result.configuration_defaults_description,
            target_entity_id=pipeline_entity_id,

        ))

    return f"Successfully submitted run for SWE agent, the run id is {run.id}"


async def get_entity_details_tool(ctx: RunContext[OrchestratorAgentDeps], entity_ids: List[uuid.UUID]) -> str:
    """
    Get the details of the entities with the provided IDs.
    """
    entity_details_response = await get_entity_details(ctx.deps.user_id, entity_ids)
    return "\n\n".join([detail.description for detail in entity_details_response.entity_details])
