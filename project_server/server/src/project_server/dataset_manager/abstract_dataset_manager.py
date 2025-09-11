import uuid
import json
from io import BytesIO
from typing import List, Optional, Union
from dataclasses import asdict
from abc import ABC, abstractmethod

from project_server.dataset_manager.dataclasses import (
    DatasetCreateWithRawData,
    ObjectGroupCreateWithRawData,
    DatasetWithRawData,
    ObjectGroupWithRawData,

)
from project_server.client import ProjectClient
from project_server.client.requests.data_objects import post_dataset
from project_server.client.client import FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetWithObjectGroups,
    ObjectGroupCreate,
    MetadataDataframe,
    ObjectGroupInDB
)


from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure
)

from synesis_data_structures.time_series.definitions import (
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID
)


class AbstractDatasetManager(ABC):

    def __init__(self, bearer_token: str):
        self.client = ProjectClient(bearer_token)

    @abstractmethod
    def get_data_group_with_raw_data(self, group_id: uuid.UUID) -> ObjectGroupWithRawData:
        """
        - Read metadata from main server or local
            - Currently only local supported (we save a copy of the metadata locally), but for small metadata we can read from main server
        - Read raw data from local / s3 storage
        - Return data structure
        """

    @abstractmethod
    def get_dataset_with_raw_data(self, dataset_id: uuid.UUID) -> DatasetWithRawData:
        """
        - Get all groups in dataset from main server
        - Read all data structures to compose Dataset
        """

    @abstractmethod
    async def upload_dataset(self, dataset: DatasetCreateWithRawData, output_json: bool = False) -> Union[str, DatasetWithRawData]:
        """
        - Upload dataset to main server
        NB: Implementation must call self._upload_dataset_metadata_to_main_server(dataset)
        """

    # Private methods

    def _process_object_group_for_upload(self, group: ObjectGroupCreateWithRawData) -> tuple[ObjectGroupCreate, list[FileInput]]:
        files = []
        object_group_create = ObjectGroupCreate(
            name=group.name,
            entity_id_name=group.entity_id_name,
            description=group.description,
            structure_type=group.structure_type,
            metadata_dataframes=[]
        )

        # Note that we only append the metadata files and not the raw data, since we keep the raw data here at the project server
        if isinstance(group.structure, TimeSeriesStructure):

            if group.structure.entity_metadata is not None and not group.structure.entity_metadata.empty:
                buffer = BytesIO()
                group.structure.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{uuid.uuid4()}.parquet"
                files.append(FileInput(
                    field_name="files",
                    filename=filename,
                    file_data=buffer.getvalue(),
                    content_type="application/octet-stream"
                ))

                object_group_create.metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=ENTITY_METADATA_SECOND_LEVEL_ID
                    )
                )

            if group.structure.feature_information is not None and not group.structure.feature_information.empty:
                buffer = BytesIO()
                group.structure.feature_information.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{uuid.uuid4()}.parquet"
                files.append(FileInput(
                    field_name="files",
                    filename=filename,
                    file_data=buffer.getvalue(),
                    content_type="application/octet-stream"
                ))

                object_group_create.metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=FEATURE_INFORMATION_SECOND_LEVEL_ID
                    )
                )

        elif isinstance(group.structure, TimeSeriesAggregationStructure):

            if group.structure.time_series_aggregation_inputs is not None and not group.structure.time_series_aggregation_inputs.empty:
                buffer = BytesIO()
                group.structure.time_series_aggregation_inputs.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{uuid.uuid4()}.parquet"
                files.append(
                    ("files", (filename, buffer, "application/octet-stream")))

                object_group_create.metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID
                    )
                )

            if group.structure.entity_metadata is not None and not group.structure.entity_metadata.empty:
                buffer = BytesIO()
                group.structure.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{uuid.uuid4()}.parquet"
                files.append(
                    FileInput(
                        field_name="files",
                        filename=filename,
                        file_data=buffer.getvalue(),
                        content_type="application/octet-stream"
                    ))

                object_group_create.metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=ENTITY_METADATA_SECOND_LEVEL_ID
                    )
                )

            if group.structure.feature_information is not None and not group.structure.feature_information.empty:
                buffer = BytesIO()
                group.structure.feature_information.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{uuid.uuid4()}.parquet"
                files.append(
                    FileInput(
                        field_name="files",
                        filename=filename,
                        file_data=buffer.getvalue(),
                        content_type="application/octet-stream"
                    ))

                object_group_create.metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=FEATURE_INFORMATION_SECOND_LEVEL_ID
                    )
                )

        return object_group_create, files

    async def _add_raw_create_data_to_dataset_from_api(self, dataset_from_api: DatasetWithObjectGroups, dataset_create: DatasetCreateWithRawData) -> DatasetWithRawData:
        """
        Associate raw data from the original dataset creation with the metadata returned from the main server.
        Needed to associate the created dataset with its metadata to store it properly locally.
        """

        def _find_group_by_name(group_name: str, groups: List[ObjectGroupInDB]) -> ObjectGroupInDB:
            # Maybe not the best solution to use names as IDs, could alternatively use temporary IDs to associate the create data with the metadata
            if len([group for group in groups if group.name == group_name]) > 1:
                raise ValueError(
                    f"Multiple groups with the same name: {group_name}")

            for group in groups:
                if group.name == group_name:
                    return group

            raise ValueError(f"Group not found: {group_name}")

        primary_group_with_raw_data = ObjectGroupWithRawData(
            id=dataset_from_api.primary_object_group.id,
            dataset_id=dataset_from_api.id,
            name=dataset_from_api.primary_object_group.name,
            description=dataset_from_api.primary_object_group.description,
            role=dataset_from_api.primary_object_group.role,
            structure_type=dataset_from_api.primary_object_group.structure_type,
            created_at=dataset_from_api.primary_object_group.created_at,
            updated_at=dataset_from_api.primary_object_group.updated_at,
            structure=dataset_create.primary_object_group.structure
        )

        annotated_groups_with_raw_data = []
        for group_create_with_raw_data in dataset_create.annotated_object_groups:
            group_metadata = _find_group_by_name(
                group_create_with_raw_data.name,
                dataset_from_api.annotated_object_groups
            )
            if group_metadata:
                annotated_groups_with_raw_data.append(
                    ObjectGroupWithRawData(
                        id=group_metadata.id,
                        dataset_id=dataset_from_api.id,
                        name=group_metadata.name,
                        description=group_metadata.description,
                        role=group_metadata.role,
                        structure_type=group_metadata.structure_type,
                        created_at=group_metadata.created_at,
                        updated_at=group_metadata.updated_at,
                        structure=group_create_with_raw_data.structure
                    )
                )

        computed_groups_with_raw_data = []
        for group_create_with_raw_data in dataset_create.computed_object_groups:
            group_metadata = _find_group_by_name(
                group_create_with_raw_data.name,
                dataset_from_api.computed_object_groups
            )
            if group_metadata:
                computed_groups_with_raw_data.append(
                    ObjectGroupWithRawData(
                        id=group_metadata.id,
                        dataset_id=dataset_from_api.id,
                        name=group_metadata.name,
                        description=group_metadata.description,
                        role=group_metadata.role,
                        structure_type=group_metadata.structure_type,
                        created_at=group_metadata.created_at,
                        updated_at=group_metadata.updated_at,
                        structure=group_create_with_raw_data.structure
                    )
                )

        return DatasetWithRawData(
            id=dataset_from_api.id,
            user_id=dataset_from_api.user_id,
            name=dataset_from_api.name,
            description=dataset_from_api.description,
            modality=dataset_from_api.modality,
            created_at=dataset_from_api.created_at,
            updated_at=dataset_from_api.updated_at,
            primary_object_group=primary_group_with_raw_data,
            annotated_object_groups=annotated_groups_with_raw_data,
            computed_object_groups=computed_groups_with_raw_data
        )

    async def _upload_dataset_metadata_to_main_server(self, dataset_create: DatasetCreateWithRawData) -> DatasetWithRawData:
        """
        - Upload dataset metadata to main server
        """
        files = []

        # Process primary object group
        primary_metadata, primary_files = self._process_object_group_for_upload(
            dataset_create.primary_object_group)
        files.extend(primary_files)

        dataset_create_api = DatasetCreate(
            name=dataset_create.name,
            description=dataset_create.description,
            modality=dataset_create.modality,
            primary_object_group=primary_metadata,
            annotated_object_groups=[],
            computed_object_groups=[]
        )

        # Process annotated object groups
        for group in dataset_create.annotated_object_groups:
            group_metadata, group_files = self._process_object_group_for_upload(
                group)
            files.extend(group_files)
            dataset_create_api.annotated_object_groups.append(group_metadata)

        # Process derived object groups
        for group in dataset_create.computed_object_groups:
            group_metadata, group_files = self._process_object_group_for_upload(
                group)
            files.extend(group_files)
            dataset_create_api.computed_object_groups.append(group_metadata)

        dataset_from_api = await post_dataset(self.client, files, dataset_create_api)

        dataset_with_raw_data = await self._add_raw_create_data_to_dataset_from_api(dataset_from_api, dataset_create)

        return dataset_with_raw_data
