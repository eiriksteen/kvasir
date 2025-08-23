import uuid
from typing import List, Literal, Callable, Tuple, Optional
from datetime import datetime, timezone
from pydantic_ai.messages import ModelMessage
from pydantic_ai.agent import AgentRunResult

from synesis_api.modules.runs.service import create_run_message, create_run, create_run_message_pydantic, update_run_status
from synesis_api.redis import get_redis
from synesis_api.agents.swe.agent import swe_agent
from synesis_api.agents.swe.output import (
    SWEAgentOutput,
    PlanningOutput,
    ImplementationOutputWithScript,
    SetupAgentOutputWithScript,
)
from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.worker import logger


class SWEAgentRunner:

    def __init__(
            self,
            user_id: str,
            conversation_id: uuid.UUID,
            parent_run_id: uuid.UUID,
            log_to_parent_run: bool = True
    ):

        self.swe_agent = swe_agent
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.parent_run_id = parent_run_id
        self.run_id = None
        self.log_to_parent_run = log_to_parent_run
        self.redis_stream = get_redis()

    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
        """Log a message to Redis stream"""

        log_run_id = self.parent_run_id if self.log_to_parent_run else self.run_id

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(log_run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(log_run_id), message)

        if write_to_db:
            await create_run_message(message_type, log_run_id, content)

    def get_run_id(self) -> uuid.UUID:
        return self.run_id

    async def _run_planning(self, prompt_content: str) -> AgentRunResult:

        user_prompt = f"We are now in the planning stage. Create the implementation plan for:\n\n{prompt_content}"

        result = await self.swe_agent.run(user_prompt, deps=SWEAgentDeps())

        await self._log_message_to_redis(f"Implementation planning completed!", "result", write_to_db=True)

        return result

    async def _run_setup(
            self,
            prompt_content: str,
            message_history: Optional[List[ModelMessage]] = None) -> AgentRunResult:

        user_prompt = f"We are now in the setup stage. Create the setup script!"

        # If no message history (where the deliverable desc is contained), we must include it in the prompt
        if message_history is None:
            user_prompt = f"{user_prompt}\n\nThis is the deliverable description:\n\n{prompt_content}"

        result = await self.swe_agent.run(user_prompt, deps=SWEAgentDeps(), message_history=message_history)

        await self._log_message_to_redis(f"Implementation setup completed!", "result", write_to_db=True)

        return result

    async def _run_implementation(
            self,
            prompt_content: str,
            setup_script: str,
            message_history: Optional[List[ModelMessage]] = None,
            validation_fns: List[Callable] = []
    ) -> AgentRunResult:

        user_prompt = (
            "We are now in the implementation stage. Implement the script!"
            f"This is the setup script with the packages you have to work with (it has already been run):\n\n{setup_script}"
        )

        if message_history is None:
            user_prompt = f"{user_prompt}\n\nThis is the deliverable description:\n\n{prompt_content}"

        result = await self.swe_agent.run(
            user_prompt,
            deps=SWEAgentDeps(implementation_validation_fns=validation_fns),
            message_history=message_history
        )

        await self._log_message_to_redis(f"Implementation completed!", "result", write_to_db=True)

        return result

    async def _save_results(
            self,
            setup_result: AgentRunResult,
            implementation_result: AgentRunResult,
            plan_result: Optional[AgentRunResult] = None
    ):

        if plan_result is not None:
            await create_run_message_pydantic(self.run_id, plan_result.new_messages_json())

        await create_run_message_pydantic(self.run_id, setup_result.new_messages_json())
        await create_run_message_pydantic(self.run_id, implementation_result.new_messages_json())

    async def __call__(
        self,
        prompt_content: str,
        implementation_validation_fns: List[Callable],
        run_planning: bool = True,
        resume: bool = False
    ) -> SWEAgentOutput:

        run = await create_run(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            type="swe",
            parent_run_id=self.parent_run_id
        )
        self.run_id = run.id

        try:

            if run_planning:
                plan_result = await self._run_planning(prompt_content)
                plan_messages = plan_result.new_messages()
            else:
                plan_result, plan_messages = None, None

            setup_result = await self._run_setup(prompt_content, plan_messages)

            implementation_result = await self._run_implementation(
                prompt_content,
                setup_result.output.script,
                # Don't include the setup messages as they aren't really relevant (excluding the setup script)
                plan_messages,
                implementation_validation_fns
            )

            # We only save the run messages as the outputs are dealt with by the caller
            await self._save_results(plan_result, setup_result, implementation_result)

        except Exception as e:
            await self._log_message_to_redis(f"Error running SWE agent: {e}", "error", write_to_db=True)
            logger.error(f"Error running SWE agent: {e}")
            await update_run_status(self.run_id, "failed")
            raise e

        else:
            return SWEAgentOutput(
                plan=plan_result.output,
                setup=setup_result.output,
                implementation=implementation_result.output
            )
