import uuid
import json
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from typing import Annotated

from project_server.app_secrets import MODEL_WEIGHTS_DIR
from project_server.worker import broker
from project_server.client import (
    ProjectClient,
    get_model_entities_by_ids,
    get_user_pipeline,
    post_pipeline_output_dataset,
    post_pipeline_output_model_entity,
    post_pipeline_run_object,
    post_model_entity_implementation,
    post_add_entity,
    patch_pipeline_run_status
)
from project_server.utils.code_utils import run_python_code_in_container
from synesis_schemas.main_server import (
    Dataset,
    ModelEntityCreate,
    ModelEntityImplementationCreate,
    AddEntityToProject,
    GetModelEntityByIDsRequest,
    PipelineRunStatusUpdate,
    PipelineRunDatasetOutputCreate,
    PipelineRunModelEntityOutputCreate
)
from synesis_schemas.project_server import RunPipelineRequest
from project_server.auth import TokenData, decode_token
from project_server.agents.swe.agent import swe_agent
from project_server.agents.swe.sandbox_code import add_submit_results_call_to_main
from project_server.worker import logger


router = APIRouter()


class PipelineDatasetNamingOutput(BaseModel):
    dataset_name: str
    dataset_description: str


@broker.task(retry_on_error=False)
async def run_pipeline_task(
        bearer_token: str,
        pipeline_id: uuid.UUID,
        project_id: uuid.UUID):

    client = ProjectClient(bearer_token)
    pipeline_run = await post_pipeline_run_object(client, pipeline_id)

    try:
        pipeline_obj = await get_user_pipeline(client, pipeline_id)
        model_entities = await get_model_entities_by_ids(client, GetModelEntityByIDsRequest(model_entity_ids=[me_id for me_id in pipeline_obj.inputs.model_entity_ids]))

        with open(pipeline_obj.implementation.implementation_script.path) as f:
            pipeline_code = f.read()

        pipeline_input_args = pipeline_obj.implementation.args
        logger.info(f"PIPELINE INPUT ARGS: {pipeline_input_args}")
        weights_save_dir_dict = {}
        for me in model_entities:
            if me.implementation and me.implementation.weights_save_dir is None:
                weights_save_dir_dict[me.id] = str(
                    MODEL_WEIGHTS_DIR / f"{uuid.uuid4()}")
                pipeline_input_args[f"{me.implementation.model_implementation.python_class_name}_config"][
                    "weights_save_dir"] = weights_save_dir_dict[me.id]

        for weights_save_dir in weights_save_dir_dict.values():
            Path(weights_save_dir).mkdir(parents=True, exist_ok=True)

        dataset_name_run = await swe_agent.run(
            f"Pick a short and concise name and description for the dataset outputted by the following pipeline: \n\n{pipeline_obj.model_dump_json(indent=2)}",
            output_type=PipelineDatasetNamingOutput
        )

        dataset_name = dataset_name_run.output.dataset_name
        dataset_description = dataset_name_run.output.dataset_description

        code_to_run = add_submit_results_call_to_main(
            implementation_script=pipeline_code,
            pipeline_id=str(pipeline_id),
            dataset_name=dataset_name,
            dataset_description=dataset_description,
            bearer_token=bearer_token,
            input_args=pipeline_input_args
        )

        logger.info(
            f"THE FULL CODE TO RUN (path: {pipeline_obj.implementation.implementation_script.path})")
        logger.info("--------------------------------")
        logger.info(code_to_run)
        logger.info("--------------------------------")

        out, err = await run_python_code_in_container(code_to_run)

        if err:
            raise RuntimeError(err)

        out_obj = Dataset(**json.loads(out))

        await post_pipeline_output_dataset(client, pipeline_id, PipelineRunDatasetOutputCreate(dataset_id=out_obj.id))
        await post_add_entity(client, AddEntityToProject(
            project_id=project_id,
            entity_type="dataset",
            entity_id=out_obj.id
        ))

        logger.info(
            f"Weights save dir dict: {weights_save_dir_dict}")

        new_model_entities = [
            await post_model_entity_implementation(client, ModelEntityImplementationCreate(
                model_implementation_id=me.implementation.model_implementation.id,
                model_entity_create=ModelEntityCreate(
                    name=f"{me.implementation.model_implementation.definition.name} fitted",
                    description=f"{me.implementation.model_implementation.description} fitted"
                ),
                weights_save_dir=weights_save_dir_dict[me.id],
                pipeline_id=pipeline_id,
                config={**me.implementation.config,
                        "weights_save_dir": weights_save_dir_dict[me.id]}
            )) for me in model_entities if me.id in weights_save_dir_dict and me.implementation
        ]

        for model_entity in new_model_entities:
            await post_pipeline_output_model_entity(client, pipeline_id, PipelineRunModelEntityOutputCreate(model_entity_id=model_entity.id))
            await post_add_entity(client, AddEntityToProject(
                project_id=project_id,
                entity_type="model_entity",
                entity_id=model_entity.id
            ))

        await patch_pipeline_run_status(client, pipeline_run.id, PipelineRunStatusUpdate(status="completed"))

    except Exception as e:
        await patch_pipeline_run_status(client, pipeline_run.id, PipelineRunStatusUpdate(status="failed"))
        raise e


@router.post("/run-pipeline")
async def run_pipeline(
        request: RunPipelineRequest,
        token_data: Annotated[TokenData, Depends(decode_token)] = None):

    await run_pipeline_task.kiq(
        bearer_token=token_data.bearer_token,
        pipeline_id=request.pipeline_id,
        project_id=request.project_id
    )
