import uuid
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.agent import Agent, AgentRunResult, OutputSpec
from pydantic_ai.tools import AgentDepsT
from abc import ABC, abstractmethod
from typing import Literal, Optional
from datetime import datetime, timezone

from project_server.client import post_run_message, post_run_message_pydantic, post_run, patch_run_status
from project_server.redis import get_redis
from project_server.client import ProjectClient
from project_server.worker import logger
from project_server.agents.tool_descriptions import TOOL_DESCRIPTIONS
from synesis_schemas.main_server import RunMessageCreate, RunMessageCreatePydantic, RunCreate, RunStatusUpdate


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

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def _save_results(self, *args, **kwargs):
        pass

    async def _create_run_if_not_exists(self):
        if self.run_id is None:
            run = await post_run(self.project_client, RunCreate(
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
            await self._log_message(success_message, "result", write_to_db=True)

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
            await self._log_message(error_message, "error", write_to_db=True)

    async def _run_agent(
        self,
        prompt_content: str,
        deps: Optional[AgentDepsT] = None,
        output_type: Optional[OutputSpec] = None
    ) -> AgentRunResult:

        assert self.agent is not None, "Agent is not set"

        async with self.agent.iter(
                prompt_content,
                deps=deps,
                output_type=output_type,
                message_history=self.message_history) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                if event.part.tool_name in TOOL_DESCRIPTIONS:
                                    message = TOOL_DESCRIPTIONS[event.part.tool_name]
                                else:
                                    message = f"Calling tool {event.part.tool_name}"
                                await self._log_message(message, "tool_call", write_to_db=True)

        await self._update_agent_state(run.result)
        return run.result

    async def _log_message(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True,
            target: Literal["redis", "taskiq", "both"] = "both"
    ):
        """Log a message to Redis stream"""

        log_run_id = self.parent_run_id if self.log_to_parent_run and self.parent_run_id else self.run_id

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(log_run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        if target == "redis" or target == "both":
            await self.redis_stream.xadd(str(log_run_id), message)
        if target == "taskiq" or target == "both":
            logger.info(message)

        if write_to_db:
            await post_run_message(self.project_client, RunMessageCreate(
                type=message_type,
                run_id=log_run_id,
                content=content
            ))
