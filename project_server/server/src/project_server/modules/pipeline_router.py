import uuid
from pydantic import BaseModel, model_validator
from fastapi import APIRouter, Depends
from typing import Annotated, Optional

from project_server.worker import broker
from project_server.client import (
    ProjectClient,
    get_model_entities_by_ids,
    get_pipelines_by_ids,
    patch_pipeline_run_status
)
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.agents.extraction.runner import run_extraction_task
from synesis_schemas.main_server import (
    GetModelEntityByIDsRequest,
    PipelineRunStatusUpdate,
    GetPipelinesByIDsRequest
)
from synesis_schemas.main_server import RunPipelineRequest
from synesis_schemas.project_server import RunExtractionRequest
from project_server.auth import TokenData, decode_token
from project_server.worker import logger
from project_server.utils.code_utils import run_shell_code_in_container


router = APIRouter()


class PipelineRunSettingsOutput(BaseModel):
    dataset_name: str
    dataset_description: str
    bash_script: str
    python_code_to_append: Optional[str] = None

    @model_validator(mode='after')
    def validate_at_least_one_code_field(self):
        if self.bash_script is None and self.python_code_to_append is None:
            raise ValueError(
                "At least one of bash_script or python_code_to_append must be provided")
        return self


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        user_id: uuid.UUID,
        bearer_token: str,
        run_request: RunPipelineRequest):

    client = ProjectClient(bearer_token)

    assert run_request.run_id is not None, "Run must be initiated at the main server"
    run_id = run_request.run_id

    try:
        pipeline_objs = await get_pipelines_by_ids(client, GetPipelinesByIDsRequest(pipeline_ids=[run_request.pipeline_id]))

        if len(pipeline_objs) == 0:
            raise ValueError(f"Pipeline {run_request.pipeline_id} not found")

        pipeline_obj = pipeline_objs[0]
        model_entities = await get_model_entities_by_ids(client, GetModelEntityByIDsRequest(model_entity_ids=[me_id for me_id in pipeline_obj.inputs.model_entity_ids]))

        if len(model_entities):
            model_entity_section = f"The user has provided the following model entities to use: <model_entities>\n{model_entities}\n</model_entities> "
        else:
            model_entity_section = ""

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
            f"The pipeline to run is <pipeline_description>\n{pipeline_obj.description_for_agent}\n</pipeline_description> " +
            model_entity_section +
            f"The MANDATORY arguments are: <required arguments>\n{run_request.args}\n</arguments> " +
            "Go!"
        )

        swe_output = await swe_runner(swe_prompt)
        bash_script = swe_output.main_script.content

        logger.info(
            f"THE FULL CODE TO RUN (path: {pipeline_obj.implementation.implementation_script_path})")
        logger.info("--------------------------------")
        logger.info(bash_script)
        logger.info("--------------------------------")

        _, err = await run_shell_code_in_container(bash_script)

        if err:
            raise RuntimeError(err)

        logger.info(f"Pipeline run {run_id} completed")

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

        await patch_pipeline_run_status(client, run_id, PipelineRunStatusUpdate(status="completed"))

    except Exception as e:
        await patch_pipeline_run_status(client, run_id, PipelineRunStatusUpdate(status="failed"))
        logger.info(f"Pipeline run {run_id} failed")
        raise e


@router.post("/run-pipeline")
async def run_pipeline(
        request: RunPipelineRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_pipeline_task.kiq(
        bearer_token=token_data.bearer_token,
        pipeline_id=request.pipeline_id,
        project_id=request.project_id,
        run_id=request.run_id
    )
