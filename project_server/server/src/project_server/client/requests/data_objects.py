from typing import List, Union
from uuid import UUID
import json

from project_server.client import ProjectClient, FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    Dataset,
    ObjectGroup,
    ObjectGroupWithObjects,
    GetDatasetByIDsRequest
)


async def post_dataset(client: ProjectClient, files: List[FileInput], metadata: DatasetCreate) -> Dataset:
    response = await client.send_request(
        "post",
        "/data-objects/dataset",
        files=files,
        data={"metadata": json.dumps(metadata.model_dump(mode="json"))}
    )

    return Dataset(**response.body)


async def get_project_datasets(client: ProjectClient, project_id: UUID) -> List[Dataset]:
    response = await client.send_request("get", f"/data-objects/project-datasets/{project_id}")
    return [Dataset(**ds) for ds in response.body]


async def get_datasets_by_ids(client: ProjectClient, request: GetDatasetByIDsRequest) -> List[Dataset]:
    response = await client.send_request("get", f"/data-objects/datasets-by-ids", json=request.model_dump(mode="json"))
    return [Dataset(**ds) for ds in response.body]


async def get_dataset(client: ProjectClient, dataset_id: UUID) -> Dataset:
    response = await client.send_request("get", f"/data-objects/dataset/{dataset_id}")
    return Dataset(**response.body)


async def get_object_group(client: ProjectClient, group_id: UUID, include_objects: bool = False) -> Union[ObjectGroup,  ObjectGroupWithObjects]:
    response = await client.send_request("get", f"/data-objects/object-group/{group_id}?include_objects={include_objects}")
    if include_objects:
        return ObjectGroupWithObjects(**response.body)
    else:
        return ObjectGroup(**response.body)


async def get_object_groups_in_dataset(client: ProjectClient, dataset_id: UUID) -> List[ObjectGroupWithObjects]:
    response = await client.send_request("get", f"/data-objects/object-groups-in-dataset/{dataset_id}")
    return [ObjectGroupWithObjects(**group) for group in response.body]
