import uuid
from synesis_api.worker import logger, broker
from synesis_api.modules.automation.service import run_model_agent


@broker.task
async def run_model_job(
    project_id: uuid.UUID,
    data_path: str,
    problem_description: str,
    data_analysis: str
):

    return await run_model_agent(
        project_id, data_path, problem_description, data_analysis)
