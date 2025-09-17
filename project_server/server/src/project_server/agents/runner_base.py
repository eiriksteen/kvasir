import uuid
from pydantic_ai.messages import FunctionToolCallEvent, ModelMessage
from pydantic_ai.agent import Agent, AgentRunResult, OutputSpec
from pydantic_ai.tools import AgentDepsT
from abc import ABC, abstractmethod
from typing import Literal, Optional, List
from datetime import datetime, timezone

from project_server.client import post_run_message
from project_server.redis import get_redis
from project_server.client import ProjectClient
from project_server.worker import logger
from project_server.agents.tool_descriptions import TOOL_DESCRIPTIONS
from synesis_schemas.main_server import RunMessageCreate


class RunnerBase(ABC):

    def __init__(
            self,
            agent: Agent,
            user_id: str,
            bearer_token: str,
            run_id: Optional[uuid.UUID] = None):

        self.agent = agent
        self.user_id = user_id
        self.message_history = []
        self.run_id = run_id
        self.bearer_token = bearer_token
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)
        self.redis_stream = get_redis()
        self.logger = logger

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def _save_results(self, *args, **kwargs):
        pass

    async def _run_agent(
        self,
        prompt_content: str,
        deps: Optional[AgentDepsT] = None,
        output_type: Optional[OutputSpec] = None,
        message_history: Optional[List[ModelMessage]] = None,
    ) -> AgentRunResult:
        async with self.agent.iter(
                prompt_content,
                deps=deps,
                output_type=output_type,
                message_history=message_history) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                message = TOOL_DESCRIPTIONS[event.part.tool_name]
                                await self._log_message_to_redis(message, "tool_call", write_to_db=True)
                                self.logger.info(f"Calling tool {message}")

        return run.result

    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
        """Log a message to Redis stream"""

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(self.run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.run_id), message)

        if write_to_db:
            await post_run_message(self.project_client, RunMessageCreate(
                type=message_type,
                run_id=str(self.run_id),
                content=content
            ))
