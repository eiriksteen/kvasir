import uuid
from typing import Optional, List
from pydantic import BaseModel

from project_server.agents.analysis.agent import analysis_agent, AnalysisDeps
from project_server.worker import broker
from project_server.agents.runner_base import RunnerBase
from synesis_schemas.project_server import RunAnalysisRequest
from synesis_schemas.main_server import (
    GetModelEntityByIDsRequest,
    GetDataSourcesByIDsRequest,
    GetDatasetsByIDsRequest,
)
from project_server.client import (
    get_model_entities_by_ids,
    get_data_sources_by_ids,
    get_datasets_by_ids,
)
from project_server.worker import logger


class AnalysisReportResult(BaseModel):
    analysis_report: str
    analysis_code: str


class AnalysisAgentRunner(RunnerBase):
    def __init__(
        self,
        user_id: str,
        run_id: uuid.UUID,
        bearer_token: str,
        analysis_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        model_entity_ids: Optional[List[uuid.UUID]] = None,
        data_source_ids: Optional[List[uuid.UUID]] = None,
        dataset_ids: Optional[List[uuid.UUID]] = None,
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

        self.analysis_id = analysis_id
        self.model_entity_ids = model_entity_ids
        self.data_source_ids = data_source_ids
        self.dataset_ids = dataset_ids

    async def __call__(self, prompt_content: str):
        try:
            logger.info(
                f"Running analysis agent with prompt: {prompt_content}")
            await self._create_run_if_not_exists()
            logger.info(f"Created run for analysis agent")
            await self._prepare_deps()
            logger.info(f"Prepared dependencies for analysis agent")

            run_result = await self._run_agent(
                prompt_content=f"Solve this user prompt: {prompt_content}.",
                deps=self.deps,
                output_type=str
            )

            await self._complete_agent_run("Analysis agent run completed")

            return run_result.output

        except Exception as e:
            await self._fail_agent_run(f"Error running analysis agent: {e}")
            raise e

    async def _prepare_deps(self) -> None:
        self.model_entities = await get_model_entities_by_ids(self.project_client, GetModelEntityByIDsRequest(model_entity_ids=self.model_entity_ids))
        self.data_sources = await get_data_sources_by_ids(self.project_client, GetDataSourcesByIDsRequest(data_source_ids=self.data_source_ids))
        self.datasets = await get_datasets_by_ids(self.project_client, GetDatasetsByIDsRequest(dataset_ids=self.dataset_ids))

        deps = AnalysisDeps(
            client=self.project_client,
            run_id=self.run_id,
            project_id=self.project_id,
            analysis_id=self.analysis_id,
            model_entities_injected=self.model_entities,
            data_sources_injected=self.data_sources,
            datasets_injected=self.datasets
        )

        self.deps = deps

    async def _save_results(self, *args, **kwargs):
        """Analysis results are saved through tools during execution, no additional saving needed."""
        pass


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
        analysis_id=analysis_request.analysis_id,
        model_entity_ids=analysis_request.model_entity_ids,
        data_source_ids=analysis_request.data_source_ids,
        dataset_ids=analysis_request.dataset_ids
    )

    await runner(analysis_request.prompt_content)
