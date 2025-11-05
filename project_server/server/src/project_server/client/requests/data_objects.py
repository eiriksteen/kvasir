from typing import List, Union
from uuid import UUID
import json

from project_server.client import ProjectClient, FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    Dataset,
    ObjectGroup,
    ObjectGroupWithObjects,
    GetDatasetsByIDsRequest,
    DataObject,
    DataObjectGroupCreate,
    ObjectsFile,
    UpdateObjectGroupChartScriptRequest
)


async def post_dataset(client: ProjectClient, files: List[FileInput], metadata: DatasetCreate) -> Dataset:
    response = await client.send_request(
        "post",
        "/data-objects/dataset",
        files=files,
        data={"metadata": json.dumps(metadata.model_dump(mode="json"))}
    )

    return Dataset(**response.body)


async def post_object_group(client: ProjectClient, dataset_id: UUID, group_create: DataObjectGroupCreate, files: List[FileInput]) -> ObjectGroup:
    response = await client.send_request(
        "post",
        f"/data-objects/object-group/{dataset_id}",
        files=files,
        data={"group_create": json.dumps(group_create.model_dump(mode="json"))}
    )
    return ObjectGroup(**response.body)


async def post_data_objects(client: ProjectClient, group_id: UUID, files: List[FileInput], metadata: List[ObjectsFile]) -> List[DataObject]:
    response = await client.send_request(
        "post",
        f"/data-objects/objects/{group_id}",
        files=files,
        data={"metadata": json.dumps(
            [obj.model_dump(mode="json") for obj in metadata])}
    )
    return [DataObject(**obj) for obj in response.body]


async def get_project_datasets(client: ProjectClient, project_id: UUID) -> List[Dataset]:
    response = await client.send_request("get", f"/project/project-datasets/{project_id}")
    return [Dataset(**ds) for ds in response.body]


async def get_datasets_by_ids(client: ProjectClient, request: GetDatasetsByIDsRequest) -> List[Dataset]:
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


async def get_data_object(client: ProjectClient, object_id: UUID) -> DataObject:
    response = await client.send_request("get", f"/data-objects/data-object/{object_id}")
    return DataObject(**response.body)


async def patch_object_group_chart_script(client: ProjectClient, group_id: UUID, request: UpdateObjectGroupChartScriptRequest) -> ObjectGroup:
    response = await client.send_request(
        "patch",
        f"/data-objects/object-group/{group_id}/chart-script",
        json=request.model_dump(mode="json")
    )
    return ObjectGroup(**response.body)
