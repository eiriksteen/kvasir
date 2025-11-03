import uuid
from typing import Optional, List
from pydantic import BaseModel

from project_server.agents.analysis.agent import analysis_agent, AnalysisDeps
from project_server.agents.analysis.output import submit_final_output
from project_server.worker import broker
from project_server.agents.runner_base import RunnerBase
from synesis_schemas.project_server import RunAnalysisRequest


class AnalysisReportResult(BaseModel):
    analysis_report: str
    analysis_code: str


class AnalysisAgentRunner(RunnerBase):
    def __init__(
        self,
        user_id: str,
        run_id: uuid.UUID,
        bearer_token: str,
        target_analysis_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        input_model_entity_ids: Optional[List[uuid.UUID]] = None,
        input_data_source_ids: Optional[List[uuid.UUID]] = None,
        input_dataset_ids: Optional[List[uuid.UUID]] = None,
        input_analysis_ids: Optional[List[uuid.UUID]] = None,
    ):
        super().__init__(
            agent=analysis_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_type="analysis",
            conversation_id=conversation_id,
            project_id=project_id,
            run_id=run_id
        )

        self.target_analysis_id = target_analysis_id
        self.input_model_entity_ids = input_model_entity_ids or []
        self.input_data_source_ids = input_data_source_ids or []
        self.input_dataset_ids = input_dataset_ids or []
        self.input_analysis_ids = input_analysis_ids or []

    async def __call__(self, prompt_content: str):
        try:
            await self._setup_project_container()
            await self._create_run_if_not_exists()
            await self._prepare_deps()

            run_result = await self._run_agent(
                prompt_content=f"Solve this user prompt: {prompt_content}.",
                deps=self.deps,
                output_type=submit_final_output
            )

            await self._complete_agent_run("Analysis agent run completed")

            return run_result.output

        except Exception as e:
            await self._fail_agent_run(f"Error running analysis agent: {e}")
            raise e

    async def _prepare_deps(self) -> None:
        self.deps = AnalysisDeps(
            client=self.project_client,
            run_id=self.run_id,
            project_id=self.project_id,
            analysis_id=self.target_analysis_id,
            model_entities_injected=self.input_model_entity_ids,
            data_sources_injected=self.input_data_source_ids,
            datasets_injected=self.input_dataset_ids,
            analyses_injected=self.input_analysis_ids
        )


@broker.task
async def run_analysis_task(
    user_id: uuid.UUID,
    bearer_token: str,
    analysis_request: RunAnalysisRequest

):
    runner = AnalysisAgentRunner(
        user_id=user_id,
        run_id=analysis_request.run_id,
        bearer_token=bearer_token,
        conversation_id=analysis_request.conversation_id,
        project_id=analysis_request.project_id,
        target_analysis_id=analysis_request.target_analysis_id,
        input_model_entity_ids=analysis_request.input_model_entity_ids,
        input_data_source_ids=analysis_request.input_data_source_ids,
        input_dataset_ids=analysis_request.input_dataset_ids,
        input_analysis_ids=analysis_request.input_analysis_ids
    )

    await runner(analysis_request.prompt_content)
