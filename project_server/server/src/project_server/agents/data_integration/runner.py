import uuid
from typing import List

from project_server.agents.data_integration.agent import data_integration_agent, DataIntegrationAgentDeps
from project_server.agents.data_integration.output import DataIntegrationAgentOutputWithDatasetId, submit_data_integration_output
from project_server.worker import broker
from project_server.agents.runner_base import RunnerBase
from project_server.entity_manager import file_manager
from project_server.client import (
    get_data_sources_by_ids,
    post_add_entity,
    post_create_node,
)
from synesis_schemas.main_server import (
    AddEntityToProject,
    FrontendNodeCreate,
    GetDataSourcesByIDsRequest
)


class DataIntegrationRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            run_id: uuid.UUID,
            bearer_token: str):

        super().__init__(
            agent=data_integration_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_id=run_id,
            run_type="data_integration",
            conversation_id=conversation_id,
            project_id=project_id
        )

    async def __call__(
        self,
        prompt_content: str,
        data_source_ids: List[uuid.UUID]
    ):

        data_sources = await get_data_sources_by_ids(self.project_client, GetDataSourcesByIDsRequest(data_source_ids=data_source_ids))
        assert data_sources is not None, "No data sources found for the given IDs"
        await self._create_run_if_not_exists()

        try:
            run = await self._run_agent(
                prompt_content,
                deps=DataIntegrationAgentDeps(
                    data_sources=data_sources,
                    bearer_token=self.bearer_token
                ),
                output_type=submit_data_integration_output)

            await self._save_results(run.output)
            await self._complete_agent_run("Integration agent run completed")
            return run.output

        except Exception as e:
            await self._fail_agent_run(f"Error running integration agent: {e}")
            raise e

    def get_run_id(self) -> uuid.UUID:
        return self.run_id

    async def _save_results(self, output: DataIntegrationAgentOutputWithDatasetId) -> None:

        file_manager.save_script(
            f"data_integration_{self.run_id}.py",
            output.code,
            "data_integration",
            add_uuid=False,
            temporary=False,
            add_v1=True
        )

        # TODO: deal with this

        await post_add_entity(self.project_client, AddEntityToProject(
            project_id=self.project_id,
            entity_type="dataset",
            entity_id=output.dataset_id
        ))

        await post_create_node(self.project_client, FrontendNodeCreate(
            project_id=self.project_id,
            type="dataset",
            dataset_id=output.dataset_id
        ))


@broker.task(retry_on_error=False)
async def run_data_integration_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        run_id: uuid.UUID,
        data_source_ids: List[uuid.UUID],
        prompt_content: str,
        bearer_token: str):

    runner = DataIntegrationRunner(
        user_id,
        project_id,
        conversation_id,
        run_id,
        bearer_token,
    )

    result = await runner(prompt_content=prompt_content, data_source_ids=data_source_ids)

    return result
