import uuid
from io import BytesIO
from pathlib import Path
from typing import Union, List, Tuple
import pandas as pd
from abc import ABC, abstractmethod

from project_server.dataset_manager.dataclasses import (
    DatasetCreateWithRawData,
    ObjectGroupCreateWithRawData,
    DatasetWithRawData,
    ObjectGroupWithRawData,
    VariableGroupCreateWithRawData,
    RawVariableCreate
)
from project_server.client import ProjectClient
from project_server.client.requests.data_objects import post_dataset
from project_server.client.client import FileInput

from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetFull,
    ObjectGroupCreate,
    MetadataDataframe,
    VariableGroupCreate,
    VariableCreate
)


from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure
)

from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID
)

from project_server.app_secrets import INTEGRATED_DATA_DIR


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

    async def _upload_dataset_metadata_to_main_server(self, dataset_create: DatasetCreateWithRawData) -> Tuple[DatasetFull, List[Tuple[Path, pd.DataFrame]], List[Tuple[Path, dict]]]:
        """
        Upload dataset metadata to main server
        """
        files = []
        object_group_save_paths: List[Tuple[Path, pd.DataFrame]] = []
        variable_group_save_paths: List[Tuple[Path, dict]] = []

        dataset_create_api = DatasetCreate(
            name=dataset_create.name,
            description=dataset_create.description,
            object_groups=[],
            variable_groups=[]
        )

        dataset_path = INTEGRATED_DATA_DIR / str(uuid.uuid4())
        dataset_path.mkdir(parents=True, exist_ok=True)

        # Process annotated object groups
        for group in dataset_create.object_groups:
            group_metadata, group_files, paths = self._process_object_group_for_upload(
                group, dataset_path)
            files.extend(group_files)
            dataset_create_api.object_groups.append(group_metadata)
            object_group_save_paths.extend(paths)

        # Process derived object groups
        for group in dataset_create.variable_groups:
            group_metadata, path = self._process_variable_group_for_upload(
                group, dataset_path)
            dataset_create_api.variable_groups.append(group_metadata)
            variable_group_save_paths.append(path)

        dataset_from_api = await post_dataset(self.client, files, dataset_create_api)

        return dataset_from_api, object_group_save_paths, variable_group_save_paths

    def _process_object_group_for_upload(self, group: ObjectGroupCreateWithRawData, dataset_path: Path) -> Tuple[ObjectGroupCreate, List[FileInput], List[Tuple[Path, pd.DataFrame]]]:
        files = []
        group_save_path = dataset_path / str(uuid.uuid4())
        group_save_path.mkdir(parents=True, exist_ok=True)
        object_group_create = ObjectGroupCreate(
            name=group.name,
            entity_id_name=group.entity_id_name,
            description=group.description,
            structure_type=group.structure_type,
            save_path=str(group_save_path),
            metadata_dataframes=[]
        )
        group_save_paths: List[Tuple[Path, pd.DataFrame]] = []

        # Note that we only append the metadata files and not the raw data, since we keep the raw data here at the project server
        if isinstance(group.structure, TimeSeriesStructure):

            time_series_save_path = group_save_path / \
                f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet"
            group_save_paths.append(
                (time_series_save_path, group.structure.time_series_data))

            if group.structure.entity_metadata is not None and not group.structure.entity_metadata.empty:
                buffer = BytesIO()
                group.structure.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet"
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
                group_save_paths.append(
                    (group_save_path / filename, group.structure.entity_metadata))

            if group.structure.feature_information is not None and not group.structure.feature_information.empty:
                buffer = BytesIO()
                group.structure.feature_information.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet"
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

                group_save_paths.append(
                    (group_save_path / filename, group.structure.feature_information))

        elif isinstance(group.structure, TimeSeriesAggregationStructure):

            time_series_aggregation_outputs_save_path = group_save_path / \
                f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet"
            group_save_paths.append(
                (time_series_aggregation_outputs_save_path, group.structure.time_series_aggregation_outputs))

            if group.structure.time_series_aggregation_inputs is not None and not group.structure.time_series_aggregation_inputs.empty:
                buffer = BytesIO()
                group.structure.time_series_aggregation_inputs.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet"
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
                        second_level_id=TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID
                    )
                )
                group_save_paths.append(
                    (group_save_path / filename, group.structure.time_series_aggregation_inputs))

            if group.structure.entity_metadata is not None and not group.structure.entity_metadata.empty:
                buffer = BytesIO()
                group.structure.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet"
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

                group_save_paths.append(
                    (group_save_path / filename, group.structure.entity_metadata))

            if group.structure.feature_information is not None and not group.structure.feature_information.empty:
                buffer = BytesIO()
                group.structure.feature_information.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet"
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

                group_save_paths.append(
                    (group_save_path / filename, group.structure.feature_information))

        return object_group_create, files, group_save_paths

    def _process_variable_group_for_upload(self, group: VariableGroupCreateWithRawData, dataset_path: Path) -> Tuple[VariableGroupCreate, Tuple[Path, dict]]:
        group_save_path = dataset_path / f"{uuid.uuid4()}.json"
        group_save_path: Tuple[Path, dict] = (group_save_path, group.data)

        variable_group_create = VariableGroupCreate(
            name=group.name,
            description=group.description,
            save_path=str(group_save_path),
            variables=[VariableCreate(
                name=variable.name,
                python_type=variable.python_type,
                description=variable.description
            ) for variable in group.variables]
        )

        return variable_group_create, group_save_path
