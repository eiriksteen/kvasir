import json
import uuid
import pandas as pd
from pathlib import Path
from typing import Union
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

from project_server.dataset_manager.abstract_dataset_manager import AbstractDatasetManager, DatasetCreate
from project_server.dataset_manager.dataclasses import ObjectGroupWithRawData, DatasetWithRawData, DatasetWithObjectGroupsAPI
from project_server.app_secrets import INTEGRATED_DATA_DIR


class LocalDatasetManager(AbstractDatasetManager):

    async def get_data_group(self, group_id: uuid.UUID) -> ObjectGroupWithRawData:
        group_metadata = await self._fetch_group_metadata_from_main_server(group_id)

        structure = await self._read_structure(group_metadata.dataset_id, group_id, group_metadata.structure_type)

        return ObjectGroupWithRawData(**asdict(group_metadata), structure=structure)

    async def get_dataset(self, dataset_id: uuid.UUID) -> DatasetWithRawData:
        dataset_metadata = await self._fetch_dataset_metadata_from_main_server(dataset_id)

        primary_group = await self.get_data_group(dataset_metadata.primary_object_group.id)

        annotated_groups = [await self.get_data_group(group.id)
                            for group in dataset_metadata.annotated_object_groups]

        computed_groups = [await self.get_data_group(group.id)
                           for group in dataset_metadata.computed_object_groups]

        return DatasetWithRawData(
            **asdict(dataset_metadata),
            primary_object_group=primary_group,
            annotated_object_groups=annotated_groups,
            computed_object_groups=computed_groups
        )

    async def upload_dataset(self, dataset_create: DatasetCreate, output_json: bool = False) -> Union[str, DatasetWithRawData]:

        dataset: DatasetWithRawData = await self._upload_dataset_metadata_to_main_server(dataset_create)

        # TODO: Don't use df.to_parquet(), use an async alternative to avoid blocking the event loop

        self._save_object_group(dataset.primary_object_group, dataset.id)

        for group in dataset.annotated_object_groups:
            self._save_object_group(group, dataset.id)

        for group in dataset.computed_object_groups:
            self._save_object_group(group, dataset.id)

        output_record = DatasetWithObjectGroupsAPI(**asdict(dataset))

        if output_json:
            return json.dumps(asdict(output_record))
        else:
            return output_record

    # Private methods

    async def _read_structure(self, dataset_id: uuid.UUID, group_id: uuid.UUID, structure_type: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
        """Read a structure from the local storage."""
        save_path = self._get_save_path(dataset_id, group_id)

        if structure_type == TIME_SERIES_STRUCTURE.first_level_id:
            time_series_data = None
            entity_metadata = None
            feature_information = None

            assert (
                save_path / f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet").exists(), "Time series data not found"

            time_series_data = pd.read_parquet(
                save_path / f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet")

            if (save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet").exists():
                entity_metadata = pd.read_parquet(
                    save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

            if (save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet").exists():
                feature_information = pd.read_parquet(
                    save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

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

            assert (save_path / f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet").exists(
            ), "Time series aggregation outputs not found"

            time_series_aggregation_outputs = pd.read_parquet(
                save_path / f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet")

            if (save_path / f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet").exists():
                time_series_aggregation_inputs = pd.read_parquet(
                    save_path / f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet")

            if (save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet").exists():
                entity_metadata = pd.read_parquet(
                    save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

            if (save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet").exists():
                feature_information = pd.read_parquet(
                    save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

            return TimeSeriesAggregationStructure(
                time_series_aggregation_outputs=time_series_aggregation_outputs,
                time_series_aggregation_inputs=time_series_aggregation_inputs,
                entity_metadata=entity_metadata,
                feature_information=feature_information
            )

        else:
            raise ValueError(f"Unknown structure type: {structure_type}")

    def _get_save_path(self, dataset_id: uuid.UUID, group_id: uuid.UUID) -> Path:
        """Generate save path and ensure directory exists."""
        save_path = INTEGRATED_DATA_DIR / str(dataset_id) / str(group_id)
        save_path.mkdir(parents=True, exist_ok=True)
        return save_path

    def _save_time_series_structure(self, structure: TimeSeriesStructure, save_path: Path) -> None:
        """Save TimeSeriesStructure data to files."""
        structure.time_series_data.to_parquet(
            save_path / f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet")

        if structure.entity_metadata is not None:
            structure.entity_metadata.to_parquet(
                save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

        if structure.feature_information is not None:
            structure.feature_information.to_parquet(
                save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

    def _save_time_series_aggregation_structure(self, structure: TimeSeriesAggregationStructure, save_path: Path) -> None:
        """Save TimeSeriesAggregationStructure data to files."""
        structure.time_series_aggregation_outputs.to_parquet(
            save_path / f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet")

        if structure.time_series_aggregation_inputs is not None:
            structure.time_series_aggregation_inputs.to_parquet(
                save_path / f"{TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID}.parquet")

        if structure.entity_metadata is not None:
            structure.entity_metadata.to_parquet(
                save_path / f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet")

        if structure.feature_information is not None:
            structure.feature_information.to_parquet(
                save_path / f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet")

    def _save_object_group(self, group: ObjectGroupWithRawData, dataset_id: uuid.UUID) -> None:
        """Save a single object group's data."""
        save_path = self._get_save_path(dataset_id, group.id)

        if isinstance(group.structure, TimeSeriesStructure):
            self._save_time_series_structure(group.structure, save_path)
        elif isinstance(group.structure, TimeSeriesAggregationStructure):
            self._save_time_series_aggregation_structure(
                group.structure, save_path)


local_dataset_manager = LocalDatasetManager()
