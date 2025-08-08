import uuid
from pathlib import Path
from typing import Optional, List, Literal
from datetime import datetime, timezone
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.agent import Agent
from synesis_api.modules.project.service import add_entity_to_project
from synesis_api.modules.data_sources.service import get_data_sources_by_ids
from synesis_api.auth.service import delete_api_key, create_api_key
from synesis_api.modules.runs.service import (
    create_run_message_pydantic,
    get_run_messages_pydantic,
    update_run_status,
    create_run,
    create_run_message,
    create_data_integration_run_input,
    create_data_integration_run_result,
)
from synesis_api.agents.data_integration.data_integration_agent.agent import (
    data_integration_agent,
    DataIntegrationAgentDeps,
    DataIntegrationAgentOutputWithDatasetId
)
from synesis_api.agents.chat.agent import chatbot_agent
from synesis_api.worker import broker, logger
from synesis_api.redis import get_redis
from synesis_api.modules.raw_data_storage.service import save_script_to_local_storage
from synesis_api.modules.project.schema import AddEntityToProject
from synesis_api.modules.node.service import create_node
from synesis_api.modules.node.schema import FrontendNodeCreate


class DataIntegrationRunner:

    def __init__(
            self,
            user_id: str,
            conversation_id: uuid.UUID,
            project_id: uuid.UUID,
            run_id: uuid.UUID | None = None):

        self.data_integration_agent = data_integration_agent
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.project_id = project_id
        self.run_id = run_id
        self.dataset_name = None
        self.redis_stream = get_redis()

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
            "conversation_id": str(self.conversation_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.run_id), message)

        if write_to_db:
            await create_run_message(message_type, self.run_id, content)

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

    def get_run_id(self) -> uuid.UUID:
        return self.run_id

    async def __call__(
        self,
        prompt_content: str,
        data_source_ids: Optional[List[uuid.UUID]] = None
    ):

        api_key = (await create_api_key(self.user_id)).key

        data_sources = await get_data_sources_by_ids(data_source_ids)
        paths = [
            data_source.file_path for data_source in data_sources]
        descriptions = [
            data_source.description for data_source in data_sources]
        assert data_sources is not None, "No data sources found for the given IDs"

        if self.run_id is None:
            self.run_id = uuid.uuid4()
            dataset_name = await self._create_dataset_name(prompt_content)
            await create_run(
                self.user_id,
                "integration",
                run_id=self.run_id,
                run_name=dataset_name
            )

        await create_data_integration_run_input(self.run_id, prompt_content, data_source_ids)

        try:
            deps = DataIntegrationAgentDeps(
                file_paths=[Path(path) for path in paths],
                data_source_descriptions=descriptions,
                api_key=api_key
            )

            message_history = await get_run_messages_pydantic(self.run_id)

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
                                    # print(event.part.args)
                                    explanation = event.part.args[
                                        "explanation"] if "explanation" in event.part.args else "Understanding dataset requirements"
                                    await self._log_message_to_redis(explanation, "tool_call", write_to_db=True)

            agent_output: DataIntegrationAgentOutputWithDatasetId = run.result.output

            python_code_path = save_script_to_local_storage(
                self.user_id,
                self.run_id,
                agent_output.code,
                "data_integration.py",
                "data_integration"
            )

            await create_data_integration_run_result(self.run_id, agent_output.dataset_id, agent_output.code_explanation, str(python_code_path))
            await create_run_message_pydantic(self.run_id, run.result.new_messages_json())
            await add_entity_to_project(self.project_id, AddEntityToProject(entity_type="dataset", entity_id=agent_output.dataset_id))
            await create_node(FrontendNodeCreate(project_id=self.project_id, type="dataset", dataset_id=agent_output.dataset_id))
            await self._log_message_to_redis(f"Integration agent run completed!", "result", write_to_db=True)
            await update_run_status(self.run_id, "completed")

            logger.info(
                f"Integration agent run completed for run {self.run_id}")

        except Exception as e:
            await self._log_message_to_redis(f"Error running integration agent: {e}", "error", write_to_db=True)
            logger.error(f"Error running integration agent: {e}")
            if run and run.result and run.result.new_messages:
                await create_run_message_pydantic(self.run_id, run.result.new_messages_json())
            await update_run_status(self.run_id, "failed")

            if api_key:
                await delete_api_key(self.user_id)

            raise e


@broker.task(retry_on_error=False)
async def run_data_integration_task(
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        data_source_ids: List[uuid.UUID],
        prompt_content: str):

    runner = DataIntegrationRunner(
        user_id,
        conversation_id,
        project_id,
        run_id
    )

    result = await runner(data_source_ids=data_source_ids, prompt_content=prompt_content)

    return result
