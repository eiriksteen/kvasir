import json
import uuid
import pandas as pd
from pathlib import Path
from typing import Union, List
from dataclasses import asdict

from synesis_data_structures.time_series.df_dataclasses import TimeSeriesStructure, TimeSeriesAggregationStructure
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_STRUCTURE,
    TIME_SERIES_AGGREGATION_STRUCTURE
)

from project_server.dataset_manager.abstract_dataset_manager import AbstractDatasetManager
from project_server.dataset_manager.dataclasses import ObjectGroupWithRawData, DatasetWithRawData, DatasetCreateWithRawData
from synesis_schemas.main_server import DatasetFull, DatasetSources
from project_server.client.requests.data_objects import get_object_group, get_dataset


class LocalDatasetManager(AbstractDatasetManager):

    async def get_data_group_with_raw_data(self, group_id: uuid.UUID) -> ObjectGroupWithRawData:
        group_metadata = await get_object_group(self.client, group_id)
        structure = await self._read_structure(group_metadata.save_path, group_metadata.structure_type)
        return ObjectGroupWithRawData(**asdict(group_metadata), structure=structure)

    async def get_dataset_with_raw_data(self, dataset_id: uuid.UUID) -> DatasetWithRawData:
        dataset_metadata = await get_dataset(self.client, dataset_id)

        object_groups = [await self.get_data_group_with_raw_data(group.id)
                         for group in dataset_metadata.object_groups]

        return DatasetWithRawData(
            *dataset_metadata.model_dump(),
            object_groups=object_groups,
            variable_groups=[]
        )

    async def upload_dataset(
            self,
            dataset_create: DatasetCreateWithRawData,
            data_source_ids: List[uuid.UUID],
            source_dataset_ids: List[uuid.UUID],
            pipeline_ids: List[uuid.UUID],
            output_json: bool = False) -> Union[str, DatasetFull]:

        sources = DatasetSources(
            data_source_ids=data_source_ids,
            source_dataset_ids=source_dataset_ids,
            pipeline_ids=pipeline_ids
        )

        dataset_api, group_dataframe_save_paths, variable_group_save_paths = await self._upload_dataset_metadata_to_main_server(dataset_create, sources)

        for save_path, dataframe in group_dataframe_save_paths:
            assert isinstance(
                dataframe, pd.DataFrame), "Group dataframe associated with the save path is not a pandas dataframe"
            dataframe.to_parquet(save_path, index=True)

        for save_path, data in variable_group_save_paths:
            assert isinstance(
                data, dict), "Variable group data associated with the save path is not a dictionary"
            with open(save_path, "w") as f:
                json.dump(data, f)

        if output_json:
            return dataset_api.model_dump_json()
        else:
            return dataset_api

    # Private methods

    async def _read_structure(self, group_path: Path, structure_type: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
        """Read a structure from the local storage."""

        if structure_type == TIME_SERIES_STRUCTURE.first_level_id:
            time_series_data = None
            entity_metadata = None
            feature_information = None

            assert (
                group_path / f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet").exists(), "Time series data not found"

            time_series_data = pd.read_parquet(
                group_path / f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet")

            if (group_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet").exists():
                entity_metadata = pd.read_parquet(
                    group_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

            if (group_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet").exists():
                feature_information = pd.read_parquet(
                    group_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

            return TimeSeriesStructure(
                time_series_data=time_series_data,
                entity_metadata=entity_metadata,
                feature_information=feature_information
            )

        elif structure_type == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id:
            time_series_aggregation_outputs = None
            time_series_aggregation_inputs = None
            entity_metadata = None
            feature_information = None

            assert (group_path / f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet").exists(
            ), "Time series aggregation outputs not found"

            time_series_aggregation_outputs = pd.read_parquet(
                group_path / f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet")

            if (group_path / f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet").exists():
                time_series_aggregation_inputs = pd.read_parquet(
                    group_path / f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet")

            if (group_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet").exists():
                entity_metadata = pd.read_parquet(
                    group_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

            if (group_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet").exists():
                feature_information = pd.read_parquet(
                    group_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

            return TimeSeriesAggregationStructure(
                time_series_aggregation_outputs=time_series_aggregation_outputs,
                time_series_aggregation_inputs=time_series_aggregation_inputs,
                entity_metadata=entity_metadata,
                feature_information=feature_information
            )

        else:
            raise ValueError(f"Unknown structure type: {structure_type}")
