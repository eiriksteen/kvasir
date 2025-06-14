from synesis_api.worker import broker
from synesis_api.modules.integration.service import run_integration_agent
import uuid

@broker.task
async def run_integration_job_task(job_id: uuid.UUID, api_key: str, data_directory: str, data_description: str, data_source: str):
    return await run_integration_agent(job_id, api_key, data_directory, data_description, data_source)