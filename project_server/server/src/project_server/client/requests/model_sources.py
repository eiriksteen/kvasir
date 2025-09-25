import uuid
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import ModelSourceCreate, ModelSource, MODEL_SOURCE_TYPE_TO_MODEL_SOURCE_CLASS


async def post_model_source(client: ProjectClient, model_source_data: ModelSourceCreate) -> ModelSource:
    response = await client.send_request("post", "/model-sources/model-source", json=model_source_data.model_dump(mode="json"))
    model_source_type = MODEL_SOURCE_TYPE_TO_MODEL_SOURCE_CLASS[model_source_data.type]
    return model_source_type(**response.body)


async def get_model_source(client: ProjectClient, model_source_id: uuid.UUID) -> ModelSource:
    response = await client.send_request("get", f"/model-sources/model-source/{model_source_id}")
    model_source_type = MODEL_SOURCE_TYPE_TO_MODEL_SOURCE_CLASS[response.body["type"]]
    return model_source_type(**response.body)


async def get_model_sources(client: ProjectClient) -> List[ModelSource]:
    response = await client.send_request("get", "/model-sources/model-sources")
    records = []
    for ms in response.body:
        model_source_type = MODEL_SOURCE_TYPE_TO_MODEL_SOURCE_CLASS[ms["type"]]
        records.append(model_source_type(**ms))
    return records
