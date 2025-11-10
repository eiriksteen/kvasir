import uuid
from abc import ABC, abstractmethod
from typing import Literal, Optional, List
from pydantic_ai import FunctionToolset
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.agent import Agent, AgentRunResult, OutputSpec
from pydantic_ai.tools import AgentDepsT

from project_server.client import post_run_message, post_run_message_pydantic, post_run, patch_run_status
from project_server.redis import get_redis
from project_server.client import ProjectClient, get_project
from project_server.worker import logger
from project_server.agents.tool_descriptions import TOOL_DESCRIPTIONS
from synesis_schemas.main_server import RunMessageCreate, RunMessageCreatePydantic, RunCreate, RunStatusUpdate, Project
from project_server.utils.docker_utils import create_project_container_if_not_exists


class RunnerBase(ABC):

    def __init__(
        self,
        agent: Optional[Agent],
        user_id: str,
        bearer_token: str,
        run_type: str,
        run_id: Optional[uuid.UUID] = None,
        conversation_id: Optional[uuid.UUID] = None,
        project_id: Optional[uuid.UUID] = None,
        parent_run_id: Optional[uuid.UUID] = None,
        log_to_parent_run: bool = False
    ):

        self.agent = agent
        self.user_id = user_id
        self.run_type = run_type
        self.conversation_id = conversation_id
        self.project_id = project_id
        self.parent_run_id = parent_run_id
        self.message_history = []
        self.message_history_json = None
        self.run_id = run_id
        self.bearer_token = bearer_token
        self.log_to_parent_run = log_to_parent_run
        self.project_client = ProjectClient(bearer_token)
        self.redis_stream = get_redis()
        self.project: Project | None = None

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        pass

    async def _run_agent(
        self,
        prompt_content: str,
        deps: Optional[AgentDepsT] = None,
        output_type: Optional[OutputSpec] = None,
        toolsets: Optional[List[FunctionToolset]] = None
    ) -> AgentRunResult:

        assert self.agent is not None, "Agent is not set"

        async with self.agent.iter(
                prompt_content,
                deps=deps,
                output_type=output_type,
                toolsets=toolsets,
                message_history=self.message_history) as agent_run:
            async for node in agent_run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(agent_run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                if event.part.tool_name in TOOL_DESCRIPTIONS:
                                    message = TOOL_DESCRIPTIONS[event.part.tool_name]
                                else:
                                    message = f"Calling tool {event.part.tool_name}"
                                await self._log_message(
                                    content=message,
                                    type="tool_call"
                                )

        await self._update_agent_state(agent_run.result)
        return agent_run.result

    async def _log_message(self,
                           content: str,
                           type: Literal["tool_call", "result", "error"],
                           write_to_db: int = 1,
                           target: Literal["redis", "taskiq", "both"] = "both"):

        log_run_id = self.parent_run_id if self.log_to_parent_run and self.parent_run_id else self.run_id

        if target == "redis" or target == "both":
            await self.redis_stream.xadd(str(log_run_id), RunMessageCreate(
                type=type,
                run_id=log_run_id,
                content=content
            ).model_dump(mode="json"))
        if target == "taskiq" or target == "both":
            logger.info(content)

        if write_to_db:
            await post_run_message(self.project_client, RunMessageCreate(
                type=type,
                run_id=log_run_id,
                content=content
            ))

    async def _setup_project_container(self):
        if self.project is None:
            raise ValueError("self.project is required to setup container")
        await create_project_container_if_not_exists(self.project)

    async def _create_run_if_not_exists(self):
        if self.run_id is None:
            run = await post_run(self.project_client, RunCreate(
                run_name=f"{self.run_type} run",
                plan_and_deliverable_description_for_user=f"The {self.run_type} agent will run and complete the task.",
                plan_and_deliverable_description_for_agent=f"The {self.run_type} agent will run and complete the task.",
                type=self.run_type,
                conversation_id=self.conversation_id,
                project_id=self.project_id,
                parent_run_id=self.parent_run_id,
                initial_status="running"
            ))
            self.run_id = run.id

    async def _update_agent_state(self, run_result: AgentRunResult):
        self.message_history += run_result.new_messages()
        self.message_history_json = run_result.all_messages_json()

    async def _complete_agent_run(self, success_message: Optional[str] = None):
        if self.message_history_json:
            await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                run_id=self.run_id,
                content=self.message_history_json
            ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=self.run_id,
            status="completed"
        ))

        if success_message:
            await self._log_message(
                content=success_message,
                type="result"
            )

    async def _fail_agent_run(self, error_message: Optional[str] = None):
        if self.message_history_json:
            await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                run_id=self.run_id,
                content=self.message_history_json
            ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=self.run_id,
            status="failed"
        ))

        if error_message:
            await self._log_message(
                content=error_message,
                type="error"
            )
