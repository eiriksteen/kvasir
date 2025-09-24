from typing import List, Union
from uuid import UUID
import json

from project_server.client import ProjectClient, FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetFull,
    DatasetFullWithFeatures,
    ObjectGroupInDB,
    ObjectGroupWithFeatures,
    ObjectGroupWithEntitiesAndFeatures,
    GetDatasetByIDsRequest
)


async def post_dataset(client: ProjectClient, files: List[FileInput], metadata: DatasetCreate) -> DatasetFull:
    response = await client.send_request(
        "post",
        "/data-objects/dataset",
        files=files,
        data={"metadata": json.dumps(metadata.model_dump(mode="json"))}
    )

    return DatasetFull(**response.body)


async def get_project_datasets(client: ProjectClient, project_id: UUID, include_features: bool = False) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    response = await client.send_request("get", f"/data-objects/project-datasets/{project_id}?include_features={include_features}")
    if include_features:
        return [DatasetFullWithFeatures(**ds) for ds in response.body]
    else:
        return [DatasetFull(**ds) for ds in response.body]


async def get_datasets_by_ids(client: ProjectClient, request: GetDatasetByIDsRequest) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    response = await client.send_request("get", f"/data-objects/datasets-by-ids", json=request.model_dump(mode="json"))
    if request.include_features:
        return [DatasetFullWithFeatures(**ds) for ds in response.body]
    else:
        return [DatasetFull(**ds) for ds in response.body]


async def get_dataset(client: ProjectClient, dataset_id: UUID, include_features: bool = False) -> Union[DatasetFullWithFeatures, DatasetFull]:
    response = await client.send_request("get", f"/data-objects/dataset/{dataset_id}?include_features={include_features}")
    if include_features:
        return DatasetFullWithFeatures(**response.body)
    else:
        return DatasetFull(**response.body)


async def get_object_group(client: ProjectClient, group_id: UUID, include_features: bool = False, include_entities: bool = False) -> Union[ObjectGroupInDB, ObjectGroupWithFeatures, ObjectGroupWithEntitiesAndFeatures]:
    response = await client.send_request("get", f"/data-objects/object-group/{group_id}?include_features={include_features}&include_entities={include_entities}")
    if include_entities and include_features:
        return ObjectGroupWithEntitiesAndFeatures(**response.body)
    elif include_features:
        return ObjectGroupWithFeatures(**response.body)
    else:
        return ObjectGroupInDB(**response.body)


async def get_object_groups_in_dataset(client: ProjectClient, dataset_id: UUID) -> List[ObjectGroupWithEntitiesAndFeatures]:
    response = await client.send_request("get", f"/data-objects/object-groups-in-dataset/{dataset_id}")
    return [ObjectGroupWithEntitiesAndFeatures(**group) for group in response.body]
