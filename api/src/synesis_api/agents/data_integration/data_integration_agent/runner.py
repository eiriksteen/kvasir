import uuid
import json
from pathlib import Path
from typing import Optional, List, Literal
from datetime import datetime, timezone
from pydantic_ai.messages import UserPromptPart, ModelRequest, FunctionToolCallEvent
from pydantic_ai.agent import Agent
from pydantic_core import to_jsonable_python
from synesis_api.modules.jobs.service import create_job, update_job_status, get_job
from synesis_api.modules.data_integration.service import (
    create_local_integration_input,
    create_integration_result,
    get_dataset_id_from_job_id,
    delete_integration_result,
    get_local_integration_input,
    get_data_sources_by_ids,
)
from synesis_api.modules.data_objects.service import delete_dataset
from synesis_api.auth.service import delete_api_key, create_api_key
from synesis_api.modules.chat.service import (
    get_current_conversation_mode,
    enter_conversation_mode,
    create_messages_pydantic,
    get_messages_pydantic
)
from synesis_api.agents.data_integration.data_integration_agent.agent import data_integration_agent, DataIntegrationAgentDeps, DataIntegrationAgentOutputWithDatasetId
from synesis_api.agents.chat.agent import chatbot_agent
from synesis_api.worker import broker, logger
from synesis_api.redis import get_redis
from synesis_api.modules.data_warehouse.service import save_script_to_local_storage


class DataIntegrationRunner:

    def __init__(
            self,
            user_id: str,
            conversation_id: uuid.UUID,
            job_id: uuid.UUID | None = None):

        self.data_integration_agent = data_integration_agent
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.job_id = job_id
        self.dataset_name = None
        self.redis_stream = get_redis()

    async def _log_message_to_redis(self, content: str, message_type: Literal["tool_call", "result", "error", "chat"]):
        """Log a message to Redis stream"""
        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "job_id": str(self.job_id),
            "conversation_id": str(self.conversation_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.job_id), message)

    async def get_dataset_name(self) -> str:
        if self.dataset_name is None:
            raise RuntimeError("Dataset name not created")
        return self.dataset_name

    async def _create_dataset_name(self, data_description: str) -> str:
        if self.dataset_name is not None:
            raise RuntimeError("Dataset name already created")

        name = await chatbot_agent.run(
            f"Give me a nice human-readable name for a dataset with the following description: '{data_description}'. The name should be short and concise. Output just the name!"
        )
        self.dataset_name = name.output
        return self.dataset_name

    def get_job_id(self) -> uuid.UUID:
        return self.job_id

    async def __call__(
        self,
        prompt_content: str,
        data_source_ids: Optional[List[uuid.UUID]] = None,
        resume: bool = False
    ):

        redis_stream = get_redis()
        api_key = (await create_api_key(self.user_id)).key
        conversation_mode = await get_current_conversation_mode(self.conversation_id)

        if resume:
            assert self.job_id is not None, "Job ID must be provided when resuming a job"
            assert conversation_mode.mode == "data_integration", "Cannot resume a job in a non-data integration conversation"
            dataset_id = await get_dataset_id_from_job_id(self.job_id)
            integration_job = await get_job(self.job_id)

            if integration_job.status == "awaiting_approval":
                await delete_dataset(dataset_id, self.user_id)
                await delete_integration_result(dataset_id)

            resume_prompt = UserPromptPart(content=prompt_content)
            new_messages = [ModelRequest(parts=[resume_prompt])]
            messages_bytes = json.dumps(
                to_jsonable_python(new_messages)).encode("utf-8")

            await create_messages_pydantic(dataset_id, messages_bytes)

            integration_message = {
                "id": str(uuid.uuid4()),
                "type": "feedback",
                "role": "user",
                "content": prompt_content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await redis_stream.xadd(str(dataset_id), integration_message)
            integration_input = await get_local_integration_input(dataset_id)
            paths = [
                data_source.file_path for data_source in integration_input.data_sources]
            await update_job_status(dataset_id, "running")

        else:
            await enter_conversation_mode(self.conversation_id, "data_integration")

            data_sources = await get_data_sources_by_ids(data_source_ids)
            paths = [
                data_source.file_path for data_source in data_sources]
            descriptions = [
                data_source.description for data_source in data_sources]
            assert data_sources is not None, "No data sources found for the given IDs"

            if self.job_id is None:
                self.job_id = uuid.uuid4()
                dataset_name = await self._create_dataset_name(prompt_content)
                await create_job(
                    self.user_id,
                    "integration",
                    job_id=self.job_id,
                    job_name=dataset_name
                )

            await create_local_integration_input(self.job_id, prompt_content, data_source_ids)

        try:
            deps = DataIntegrationAgentDeps(
                file_paths=[Path(path) for path in paths],
                data_source_descriptions=descriptions,
                api_key=api_key
            )

            message_history = await get_messages_pydantic(self.job_id)

            async with data_integration_agent.iter(
                    prompt_content,
                    deps=deps,
                    message_history=message_history) as run:
                async for node in run:
                    if Agent.is_call_tools_node(node):
                        async with node.stream(run.ctx) as handle_stream:
                            async for event in handle_stream:
                                if isinstance(event, FunctionToolCallEvent):
                                    message = f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args}'
                                    logger.info(
                                        f"Integration agent tool call: {message}")
                                    await self._log_message_to_redis(message, "tool_call")

            await self._log_message_to_redis(f"Integration agent run completed!", "result")
            logger.info(
                f"Integration agent run completed for job {self.job_id}")

            agent_output: DataIntegrationAgentOutputWithDatasetId = run.result.output

            python_code_path = save_script_to_local_storage(
                self.user_id,
                self.job_id,
                agent_output.code,
                "data_integration.py",
                "data_integration"
            )

            streamed_nodes = await redis_stream.xread({str(self.job_id): 0}, count=None)
            integration_messages = []

            for item in streamed_nodes[0][1]:
                if item[1]["type"] in ["tool_call",
                                       "help_call",
                                       "help_response",
                                       "feedback",
                                       "intervention",
                                       "summary"]:
                    message = item[1].copy()
                    message["timestamp"] = datetime.fromisoformat(
                        message["timestamp"]).replace(tzinfo=timezone.utc)

                    if len(message_history) == 0 or message["timestamp"] > message_history[-1].parts[-1].timestamp:
                        integration_messages.append(message)

            await create_integration_result(self.job_id, agent_output.dataset_id, agent_output.code_explanation, python_code_path)
            await create_messages_pydantic(self.job_id, run.result.new_messages_json())
            await update_job_status(self.job_id, "awaiting_approval")
            await enter_conversation_mode(self.conversation_id, "chat")

        except Exception as e:
            await self._log_message_to_redis(f"Error running integration agent: {e}", "error")
            logger.error(f"Error running integration agent: {e}")

            await update_job_status(self.job_id, "failed")
            await enter_conversation_mode(self.conversation_id, "chat")

            if data_sources is not None:
                for data_source in data_sources:
                    if Path(data_source.file_path).exists():
                        Path(data_source.file_path).unlink()

            if api_key:
                await delete_api_key(self.user_id)

            raise e

        # else:
        #     return agent_output


@broker.task(retry_on_error=False)
async def run_data_integration_task(
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        job_id: uuid.UUID,
        data_source_ids: List[uuid.UUID],
        prompt_content: str):

    runner = DataIntegrationRunner(
        user_id,
        conversation_id,
        job_id
    )

    result = await runner(data_source_ids=data_source_ids, prompt_content=prompt_content)

    return result


@broker.task(retry_on_error=False)
async def resume_data_integration_task(
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        prompt_content: str):

    runner = DataIntegrationRunner(
        user_id,
        job_id
    )

    result = await runner(resume=True, prompt_content=prompt_content)

    return result
