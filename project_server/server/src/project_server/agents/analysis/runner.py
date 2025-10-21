import uuid
from typing import Optional
from pydantic import BaseModel
from pydantic_ai.messages import SystemPromptPart, ModelRequest

from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from project_server.agents.analysis.agent import analysis_agent, AnalysisDeps
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
        conversation_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None
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

    async def __call__(
            self,
            analysis_request: RunAnalysisRequest,
    ):
        try:
            system_prompt = SystemPromptPart(
                content=f"""
                    {ANALYSIS_AGENT_SYSTEM_PROMPT}
                    The user has provided the following context: {analysis_request.context_message}
                """
            )
            model_request = ModelRequest(parts=[system_prompt])
            self.message_history = analysis_request.message_history + \
                [model_request]

            await self._create_run_if_not_exists()

            analysis_deps = AnalysisDeps(
                analysis_request=analysis_request,
                client=self.project_client,
                run_id=self.run_id
            )

            run_result = await self._run_agent(
                prompt_content=f"Solve this user prompt: {analysis_request.prompt}.",
                deps=analysis_deps,
                output_type=str
            )

            await self._complete_agent_run("Analysis agent run completed")

            return run_result.output

        except Exception as e:
            await self._fail_agent_run(f"Error running analysis agent: {e}")
            raise e

    async def _save_results(self, *args, **kwargs):
        """Analysis results are saved through tools during execution, no additional saving needed."""
        pass


@broker.task
async def run_analysis_task(
    analysis_request: RunAnalysisRequest,
    bearer_token: str
):
    runner = AnalysisAgentRunner(
        user_id=analysis_request.user_id,
        run_id=analysis_request.run_id,
        bearer_token=bearer_token,
        conversation_id=analysis_request.conversation_id,
        project_id=analysis_request.project_id
    )

    await runner(analysis_request)
