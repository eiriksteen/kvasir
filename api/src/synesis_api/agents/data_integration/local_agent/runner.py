import uuid
import json
import aiofiles
from pathlib import Path
import redis
from fastapi import UploadFile
from datetime import datetime, timezone
from pydantic_ai.messages import UserPromptPart, ModelRequest
from pydantic_core import to_jsonable_python
from synesis_api.modules.jobs.service import create_job, get_job_metadata, update_job_status
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.modules.data_integration.schema import IntegrationJobLocalInput, IntegrationJobResultInDB, IntegrationAgentFeedback
from synesis_api.modules.data_integration.service import (
    create_integration_input,
    create_integration_result,
    create_integration_messages,
    get_messages_pydantic,
    create_messages_pydantic,
    get_integration_input,
    delete_integration_result,
    get_dataset_id_from_job_id
)
from synesis_api.modules.ontology.service import delete_dataset
from synesis_api.auth.service import create_api_key, delete_api_key
from synesis_api.auth.schema import User
from synesis_api.agents.data_integration.local_agent.agent import local_integration_agent, LocalIntegrationDeps
from synesis_api.agents.chat.agent import chatbot_agent
from synesis_api.worker import broker, logger
from synesis_api.redis import get_redis


@broker.task
async def run_integration_job_task(
        job_id: uuid.UUID,
        api_key: str,
        data_directory: str,
        data_description: str,
        data_source: str) -> IntegrationJobResultInDB:

    print(f"Running integration agent for job {job_id}")

    redis_stream = get_redis()

    try:

        if data_source == "local":
            integration_agent = local_integration_agent
            deps = LocalIntegrationDeps(
                api_key=api_key,
                data_directory=Path(data_directory),
                data_description=data_description,
                redis_stream=redis_stream,
                job_id=job_id
            )
        else:
            raise ValueError(
                "Invalid data source, currently only local is supported")

        message_history = await get_messages_pydantic(job_id)

        nodes = []
        async with integration_agent.iter("Restructure and integrate the data, resume or start from scratch", deps=deps, message_history=message_history) as agent_run:

            async for node in agent_run:
                nodes.append(node)
                logger.info(f"Integration agent state: {node}")
                # await redis_stream.xadd(str(job_id), {"type": "pydantic_ai_state", "role": "assistant", "content": str(node), "timestamp": datetime.now(timezone.utc).isoformat()})

            logger.info(f"Integration agent run completed for job {job_id}")

        agent_output = agent_run.result.output
        status = "awaiting_approval" if agent_output.state == "completed" else "paused"

        if status == "awaiting_approval":
            output_in_db = IntegrationJobResultInDB(
                job_id=job_id,
                **agent_output.model_dump()
            )
            await create_integration_result(output_in_db)

        streamed_nodes = await redis_stream.xread({str(job_id): 0}, count=None)
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

        await create_integration_messages(job_id, integration_messages)
        await create_messages_pydantic(job_id, agent_run.result.new_messages_json())
        await update_job_status(job_id, status)

    except Exception as e:
        logger.error(f"Error running integration agent: {e}")

        await update_job_status(job_id, "failed")

        if data_directory is not None and Path(data_directory).exists():
            for file in Path(data_directory).glob("*"):
                file.unlink()
            Path(data_directory).rmdir()

        raise e

    else:
        return agent_output


class LocalDataIntegrationRunner:

    def __init__(self, user: User, dataset_id: uuid.UUID | None = None):

        self.integration_agent = local_integration_agent
        self.user = user
        self.dataset_id = dataset_id
        self.dataset_name = None

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

    def get_dataset_id(self) -> uuid.UUID:
        return self.dataset_id

    async def resume_job_from_feedback(self, feedback: str, redis_stream: redis.Redis) -> JobMetadata:

        if self.dataset_id is None:
            raise ValueError(
                "Dataset ID not found, use the __call__ method to start from scratch")

        integration_job = await get_job_metadata(self.dataset_id)

        if integration_job.status == "completed":
            raise ValueError("Integration job is already completed")

        api_key = None

        try:
            if integration_job.status == "awaiting_approval":
                dataset_id = await get_dataset_id_from_job_id(self.dataset_id)
                await delete_dataset(dataset_id, self.user.id)
                await delete_integration_result(self.dataset_id)

            resume_prompt = UserPromptPart(content=feedback)
            new_messages = [ModelRequest(parts=[resume_prompt])]
            messages_bytes = json.dumps(
                to_jsonable_python(new_messages)).encode("utf-8")

            await create_messages_pydantic(self.dataset_id, messages_bytes)

            integration_message = {
                "id": str(uuid.uuid4()),
                "type": "feedback",
                "role": "user",
                "content": feedback,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await redis_stream.xadd(str(self.dataset_id), integration_message)

            integration_input = await get_integration_input(self.dataset_id)
            api_key = await create_api_key(self.user)

            await update_job_status(self.dataset_id, "running")

            await run_integration_job_task.kiq(
                self.dataset_id,
                api_key.key,
                str(integration_input.data_directory),
                integration_input.data_description,
                "local"
            )

            integration_job.status = "running"

            return integration_job

        except Exception as e:
            if api_key:
                await delete_api_key(self.user)
            raise RuntimeError(
                f"Failed to process the integration request: {str(e)}")

    async def __call__(self, files: list[UploadFile], data_description: str):

        if self.dataset_id is not None:
            raise ValueError(
                "Dataset ID already exists, resume the job instead")

        self.dataset_id = uuid.uuid4()

        data_directory = Path.cwd() / "data" / \
            f"{self.user.id}" / f"{self.dataset_id}"
        data_directory.mkdir(parents=True, exist_ok=True)
        dataset_name = await self._create_dataset_name(data_description)
        api_key = None

        try:

            for file in files:
                relative_path = Path(file.filename)
                target_path = data_directory / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(target_path, mode="wb") as f:
                    await f.write(await file.read())

            api_key = await create_api_key(self.user)

            integration_job = await create_job(
                self.user.id,
                "integration",
                job_id=self.dataset_id,
                job_name=dataset_name
            )

            await create_integration_input(IntegrationJobLocalInput(
                job_id=self.dataset_id,
                data_description=data_description,
                data_directory=str(data_directory)
            ), "local")

            await run_integration_job_task.kiq(
                self.dataset_id,
                api_key.key,
                str(data_directory),
                data_description,
                "local"
            )

            return integration_job

        except Exception as e:
            if data_directory and data_directory.exists():
                for file in data_directory.iterdir():
                    file.unlink()
                data_directory.rmdir()
            if api_key:
                await delete_api_key(self.user)
            raise RuntimeError(
                f"Failed to process the integration request: {str(e)}")
