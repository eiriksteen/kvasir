import uuid
from typing import List, Literal
from datetime import datetime, timezone
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.agent import Agent, AgentRunResult

from project_server.agents.data_integration.agent import data_integration_agent, DataIntegrationAgentDeps
from project_server.agents.data_integration.output import DataIntegrationAgentOutputWithDatasetId
from project_server.worker import broker, logger
from project_server.redis import get_redis
from project_server.file_manager import file_manager
from project_server.utils.pydanticai_utils import pydantic_ai_bytes_to_messages
from project_server.client import (
    ProjectClient,
    post_run,
    post_run_message,
    post_run_message_pydantic,
    patch_run_status,
    post_data_integration_run_input,
    post_data_integration_run_result,
    get_run_messages_pydantic,
    get_data_sources_by_ids,
    post_add_entity,
    post_create_node,
)
from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate,
    DataIntegrationRunInputCreate,
    DataIntegrationRunResultCreate,
    AddEntityToProject,
    FrontendNodeCreate,
    GetDataSourcesByIDsRequest
)


class DataIntegrationRunner:

    def __init__(
            self,
            user_id: str,
            project_id: uuid.UUID,
            conversation_id: uuid.UUID,
            bearer_token: str,
            run_id: uuid.UUID | None = None):

        self.data_integration_agent = data_integration_agent
        self.user_id = user_id
        self.project_id = project_id
        self.conversation_id = conversation_id
        self.run_id = run_id
        self.dataset_name = None
        self.redis_stream = get_redis()
        self.bearer_token = bearer_token
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)

    async def __call__(
        self,
        prompt_content: str,
        data_source_ids: List[uuid.UUID]
    ):

        data_sources = await get_data_sources_by_ids(self.project_client, GetDataSourcesByIDsRequest(data_source_ids=data_source_ids))
        assert data_sources is not None, "No data sources found for the given IDs"

        if self.run_id is None:
            self.run_id = uuid.uuid4()

            run_in_db = await post_run(self.project_client, RunCreate(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                type="data_integration",
            ))

            self.run_id = run_in_db.id

        await post_data_integration_run_input(self.project_client, DataIntegrationRunInputCreate(
            run_id=self.run_id,
            target_dataset_description=prompt_content,
            data_source_ids=data_source_ids
        ))

        try:
            deps = DataIntegrationAgentDeps(
                data_sources=data_sources,
                bearer_token=self.bearer_token
            )

            messages_pydantic_response = await get_run_messages_pydantic(self.project_client, self.run_id)
            message_history = pydantic_ai_bytes_to_messages(
                [m.message_list for m in messages_pydantic_response])

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
                                    await self._log_message_to_redis(f"Calling tool {event.part.tool_name!r}", "tool_call", write_to_db=True)

            await self._save_results(run.result)

            logger.info(
                f"Integration agent run completed for run {self.run_id}")

        except Exception as e:
            await self._log_message_to_redis(f"Error running integration agent: {e}", "error", write_to_db=True)
            logger.error(f"Error running integration agent: {e}")
            if run and run.result and run.result.new_messages:
                await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                    type="tool_call",
                    run_id=self.run_id,
                    content=run.result.new_messages_json()
                ))

            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))

            raise e

    def get_run_id(self) -> uuid.UUID:
        return self.run_id

    async def _save_results(self, result: AgentRunResult) -> None:

        output: DataIntegrationAgentOutputWithDatasetId = result.output

        python_code_path = file_manager.save_data_integration_script(
            self.run_id,
            "data_integration.py",
            output.code
        )

        await post_data_integration_run_result(self.project_client, DataIntegrationRunResultCreate(
            run_id=self.run_id,
            dataset_id=output.dataset_id,
            code_explanation=output.code_explanation,
            python_code_path=str(python_code_path)
        ))

        await post_add_entity(self.project_client, self.project_id, AddEntityToProject(
            entity_type="dataset",
            entity_id=output.dataset_id
        ))

        await post_create_node(self.project_client, FrontendNodeCreate(
            project_id=str(self.project_id),
            type="dataset",
            dataset_id=str(output.dataset_id)
        ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=str(self.run_id),
            status="completed"
        ))

        await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
            run_id=self.run_id,
            content=result.new_messages_json()
        ))

        await self._log_message_to_redis(f"Integration agent run completed!", "result", write_to_db=True)

    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
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

    async def _create_dataset_name(self, data_description: str) -> str:
        if self.dataset_name is not None:
            raise RuntimeError("Dataset name already created")

        name = await self.data_integration_agent.run(
            f"Give me a nice human-readable name for a dataset with the following description: '{data_description}'. The name should be short and concise. Output just the name!"
        )
        self.dataset_name = name.output
        return self.dataset_name


@broker.task(retry_on_error=False)
async def run_data_integration_task(
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        data_source_ids: List[uuid.UUID],
        prompt_content: str,
        bearer_token: str):

    runner = DataIntegrationRunner(
        user_id,
        project_id,
        conversation_id,
        bearer_token,
    )

    result = await runner(prompt_content=prompt_content, data_source_ids=data_source_ids)

    return result
