import uuid
from typing import Optional

from project_server.agents.extraction.agent import extraction_agent
from project_server.agents.extraction.deps import ExtractionDeps
from project_server.agents.extraction.output import submit_final_extraction_output
from project_server.utils.docker_utils import create_project_container_if_not_exists
from project_server.worker import broker, logger
from project_server.agents.runner_base import RunnerBase
from synesis_schemas.project_server import RunExtractionRequest
from synesis_schemas.main_server import Project
from project_server.client import get_project


class ExtractionAgentRunner(RunnerBase):
    def __init__(
        self,
        user_id: str,
        bearer_token: str,
        project_id: uuid.UUID,
        run_id: Optional[uuid.UUID] = None,
    ):
        super().__init__(
            agent=extraction_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_type="extraction",
            project_id=project_id,
            run_id=run_id
        )

    async def __call__(self, prompt_content: str):
        try:
            await self._create_run_if_not_exists()
            self.project = await get_project(self.project_client, self.project_id)
            await self._setup_project_container()

            deps = ExtractionDeps(
                client=self.project_client,
                run_id=self.run_id,
                project=self.project,
                bearer_token=self.bearer_token,
                container_name=str(self.project_id)
            )

            run_result = await self._run_agent(
                prompt_content={prompt_content},
                deps=deps,
                output_type=submit_final_extraction_output
            )

            await self._complete_agent_run("Extraction agent run completed")
            return run_result.output

        except Exception as e:
            await self._fail_agent_run(f"Error running extraction agent: {e}")
            raise e


@broker.task
async def run_extraction_task(
    user_id: uuid.UUID,
    bearer_token: str,
    extraction_request: RunExtractionRequest,
    project: Project
):

    logger.info(f"Running extraction task for project {project.id}")

    runner = ExtractionAgentRunner(
        user_id=user_id,
        run_id=extraction_request.run_id,
        bearer_token=bearer_token,
        project_id=extraction_request.project_id,
    )

    await runner(extraction_request.prompt_content)
