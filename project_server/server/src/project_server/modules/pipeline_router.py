import uuid
from fastapi import APIRouter, Depends
from typing import Annotated

from project_server.worker import broker
from project_server.client import (
    ProjectClient,
    patch_pipeline_run_status,
    post_pipeline_run
)
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.agents.extraction.runner import run_extraction_task
from project_server.auth import TokenData, decode_token
from project_server.worker import logger
from project_server.utils.code_utils import run_shell_code_in_container
from project_server.utils.agent_utils import get_entities_description
from synesis_schemas.main_server import (
    PipelineRunStatusUpdate,
    PipelineRunCreate
)
from synesis_schemas.project_server import RunExtractionRequest


router = APIRouter()


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        user_id: uuid.UUID,
        bearer_token: str,
        run_request: PipelineRunCreate):

    client = ProjectClient(bearer_token)

    try:
        pipeline_run = await post_pipeline_run(client, run_request)
        pipeline_desc = await get_entities_description(client, pipeline_ids=[run_request.pipeline_id])

        swe_runner = SWEAgentRunner(
            user_id=user_id,
            bearer_token=bearer_token,
            project_id=run_request.project_id,
            conversation_id=run_request.conversation_id
        )

        swe_prompt = (
            "The user has requested a pipeline run with specified arguments and configuration parameters. " +
            "Your job is to create the script to run to satisfy the request. " +
            "Ideally, you can just create a simple bash script that parses CLI arguments. " +
            "However, depending on the structure of the code, you may need to add some files or make some changes. " +
            "Create the most minimal possible bash script to run this pipeline. " +
            f"The pipeline information is {pipeline_desc}" +
            f"The MANDATORY arguments are: <required arguments>\n{run_request.args}\n</arguments> " +
            "Go!"
        )

        swe_output = await swe_runner(swe_prompt)
        bash_script = swe_output.main_script.content

        _, err = await run_shell_code_in_container(bash_script)

        if err:
            raise RuntimeError(err)

        logger.info(f"Pipeline run {pipeline_run.id} completed")

        # Trigger extraction agent to look for new entities after pipeline completion
        extraction_prompt = (
            "The SWE agent just completed a pipeline run. "
            "Review what the SWE agent did and look for any new entities (data sources, datasets, model entities, pipelines, or analyses) "
            "that should be added to the project. "
            f"The SWE agent's prompt was: <swe_prompt>\n{swe_prompt}\n</swe_prompt>\n\n"
            f"The SWE agent's output was: <swe_output>\n{swe_output.model_dump_json()}\n</swe_output>\n\n"
        )

        await run_extraction_task.kiq(
            user_id=user_id,
            bearer_token=bearer_token,
            extraction_request=RunExtractionRequest(
                project_id=run_request.project_id, prompt_content=extraction_prompt)
        )

        await patch_pipeline_run_status(client, pipeline_run.id, PipelineRunStatusUpdate(status="completed"))

    except Exception as e:
        await patch_pipeline_run_status(client, pipeline_run.id, PipelineRunStatusUpdate(status="failed"))
        logger.info(f"Pipeline run {pipeline_run.id} failed")
        raise e


@router.post("/run-pipeline")
async def run_pipeline(
        request: PipelineRunCreate,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_pipeline_task.kiq(
        user_id=token_data.user_id,
        bearer_token=token_data.bearer_token,
        run_request=request
    )
