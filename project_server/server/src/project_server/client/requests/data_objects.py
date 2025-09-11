from typing import List, Union
from uuid import UUID
import json

from project_server.client import ProjectClient, FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetWithObjectGroups,
    DatasetWithObjectGroupsAndFeatures,
    ObjectGroupsWithEntitiesAndFeaturesInDataset,
    ObjectGroupInDB,
    ObjectGroupWithFeatures,
    ObjectGroupWithEntitiesAndFeatures
)


async def post_dataset(client: ProjectClient, files: List[FileInput], metadata: DatasetCreate) -> DatasetWithObjectGroups:
    response = await client.send_request(
        "post",
        "/data-objects/dataset",
        files=files,
        data={"metadata": json.dumps(metadata.model_dump(mode="json"))}
    )

    return DatasetWithObjectGroups(**response.body)


async def get_datasets(client: ProjectClient, include_features: bool = False) -> List[Union[DatasetWithObjectGroupsAndFeatures, DatasetWithObjectGroups]]:
    response = await client.send_request("get", f"/data-objects/datasets?include_features={include_features}")
    if include_features:
        return [DatasetWithObjectGroupsAndFeatures(**ds) for ds in response.body]
    else:
        return [DatasetWithObjectGroups(**ds) for ds in response.body]


async def get_dataset(client: ProjectClient, dataset_id: UUID, include_features: bool = False) -> Union[DatasetWithObjectGroupsAndFeatures, DatasetWithObjectGroups]:
    response = await client.send_request("get", f"/data-objects/dataset/{dataset_id}?include_features={include_features}")
    if include_features:
        return DatasetWithObjectGroupsAndFeatures(**response.body)
    else:
        return DatasetWithObjectGroups(**response.body)


async def get_object_group(client: ProjectClient, group_id: UUID, include_features: bool = False, include_entities: bool = False) -> Union[ObjectGroupInDB, ObjectGroupWithFeatures, ObjectGroupWithEntitiesAndFeatures]:
    response = await client.send_request("get", f"/data-objects/object-group/{group_id}?include_features={include_features}&include_entities={include_entities}")
    if include_entities and include_features:
        return ObjectGroupWithEntitiesAndFeatures(**response.body)
    elif include_features:
        return ObjectGroupWithFeatures(**response.body)
    else:
        return ObjectGroupInDB(**response.body)


async def get_object_groups_in_dataset(client: ProjectClient, dataset_id: UUID) -> ObjectGroupsWithEntitiesAndFeaturesInDataset:
    response = await client.send_request("get", f"/data-objects/object-groups-in-dataset/{dataset_id}")
    return ObjectGroupsWithEntitiesAndFeaturesInDataset(**response.body)
