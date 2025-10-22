import json
import uuid
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import asdict
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from typing import Union, List, Tuple

from project_server.utils.time_series_utils import convert_datetime_to_target_tz
from project_server.entity_manager.dataset_manager.dataclasses import (
    DatasetCreateWithRawData,
    ObjectGroupCreateWithRawData,
    DatasetWithRawData,
    ObjectGroupWithRawData,
    VariableGroupCreateWithRawData
)
from project_server.client import ProjectClient
from project_server.client.requests.data_objects import post_dataset, get_object_group, get_dataset, get_data_object
from project_server.client import FileInput
from project_server.app_secrets import INTEGRATED_DATA_DIR, ANALYSIS_DIR
from project_server.worker import logger
from synesis_schemas.main_server import (
    DatasetCreate,
    Dataset,
    TimeSeriesObjectGroupCreate,
    TimeSeriesAggregationObjectGroupCreate,
    MetadataDataframe,
    VariableGroupCreate,
    DatasetSources,
)


from synesis_data_interface.structures.time_series.raw import TimeSeriesStructure
from synesis_data_interface.structures.time_series_aggregation.raw import TimeSeriesAggregationStructure
from synesis_data_interface.structures.time_series.schema import TimeSeries
from synesis_data_interface.structures.serialization import serialize_dataframes_to_api_payloads
from synesis_data_interface.structures.aggregation.serialization import serialize_raw_data_for_aggregation_object_for_api
from synesis_data_interface.structures.aggregation.schema import AggregationOutput
from synesis_data_interface.structures.base.definitions import FEATURE_INFORMATION_SECOND_LEVEL_ID, ENTITY_METADATA_SECOND_LEVEL_ID
from synesis_data_interface.structures.time_series.definitions import TIME_SERIES_DATA_SECOND_LEVEL_ID, TIME_SERIES_STRUCTURE
from synesis_data_interface.structures.time_series_aggregation.definitions import TIME_SERIES_AGGREGATION_STRUCTURE, TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID, TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID


def _get_df_schema_and_head(df: pd.DataFrame | None) -> Tuple[str | None, str | None]:
    """
    Extract schema info and head string from a dataframe.

    Args:
        df: The dataframe to extract info from, or None

    Returns:
        A tuple of (schema_string, head_string). Returns (None, None) if df is None or empty.
    """
    if df is None or df.empty:
        return None, None

    buffer = StringIO()
    df.info(buf=buffer)
    schema = buffer.getvalue()
    head = df.head().to_string()

    return schema, head


# This class sometimes returns API schemas (for sending through the API) and other times dataclasses (for use in sandbox code) and should maybe be split or streamlined
class LocalDatasetManager:

    def __init__(self, bearer_token: str):
        self.client = ProjectClient(bearer_token)

    async def get_object_group_data(self, group_id: uuid.UUID) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
        group_metadata = await get_object_group(self.client, group_id)
        data = await self._read_structure(Path(group_metadata.save_path), group_metadata.structure_type)
        return data

    async def get_dataset_with_raw_data(self, dataset_id: uuid.UUID) -> DatasetWithRawData:
        dataset_metadata = await get_dataset(self.client, dataset_id)

        object_groups = [await self.get_object_group_data(group.id)
                         for group in dataset_metadata.object_groups]

        return DatasetWithRawData(
            *{k: v for k, v in dataset_metadata.model_dump().items()
              if k not in ["object_groups", "variable_groups"]},
            object_groups=object_groups,
            variable_groups=[]
        )

    async def get_object_group_data_by_name(self, dataset_id: uuid.UUID, group_name: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
        dataset_metadata = await get_dataset(self.client, dataset_id)
        group_metadata = next(
            (group for group in dataset_metadata.object_groups if group.name == group_name), None)

        if group_metadata is None:
            raise ValueError(
                f"Object group with name '{group_name}' not found in dataset '{dataset_id}'")

        return await self.get_object_group_data(group_metadata.id)

    async def get_time_series_data_object_with_raw_data(self, time_series_id: uuid.UUID, start_date: datetime, end_date: datetime) -> TimeSeries:
        # TODO: Make more efficient
        data_object = await get_data_object(self.client, time_series_id, include_object_group=True)
        entity_id = data_object.original_id
        data = await self.get_object_group_data(data_object.object_group.id)
        assert isinstance(
            data, TimeSeriesStructure), "Object group data is not a time series data structure"
        df = data.time_series_data
        # Convert start and end date to match the timezone of the dataframe (which may be None)
        start_date = convert_datetime_to_target_tz(start_date, df)
        end_date = convert_datetime_to_target_tz(end_date, df)
        df_sliced = df.loc[([entity_id], slice(start_date, end_date)), :]
        data.time_series_data = df_sliced

        return serialize_dataframes_to_api_payloads(data)[0]

    async def upload_dataset(
            self,
            dataset_create: DatasetCreateWithRawData,
            sources: DatasetSources,
            output_json: bool = False) -> Union[str, Dataset]:

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

    async def get_aggregation_object_payload_data_by_analysis_result_id(
        self,
        analysis_id: uuid.UUID,
        analysis_result_id: uuid.UUID,
    ) -> AggregationOutput:
        file_path = ANALYSIS_DIR / \
            str(analysis_id) / str(analysis_result_id) / "output.json"

        output_data = json.load(open(file_path))
        try:
            output_data = AggregationOutput.model_validate(output_data)
        except Exception as e:
            logger.error(f"Error validating output data: {e}")
            raise e

        return output_data

    async def upload_analysis_output_to_analysis_dir(self, analysis_id: uuid.UUID, analysis_result_id: uuid.UUID, output_data: pd.DataFrame | pd.Series | float | int | str | bool | datetime | timedelta | None) -> None:
        try:
            structured_output_data = serialize_raw_data_for_aggregation_object_for_api(
                output_data)
        except Exception as e:
            logger.error(f"Error serializing output data: {e}")
            raise e

        analysis_output_path = ANALYSIS_DIR / \
            str(analysis_id) / str(analysis_result_id)
        analysis_output_path.mkdir(parents=True, exist_ok=True)
        analysis_output_filepath = analysis_output_path / "output.json"
        with open(analysis_output_filepath, "w") as f:
            json.dump(structured_output_data.model_dump(), f)

    # Private methods

    async def _upload_dataset_metadata_to_main_server(self, dataset_create: DatasetCreateWithRawData, sources: DatasetSources) -> Tuple[Dataset, List[Tuple[Path, pd.DataFrame]], List[Tuple[Path, dict]]]:
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
            variable_groups=[],
            sources=sources
        )

        dataset_path = INTEGRATED_DATA_DIR / str(uuid.uuid4())
        dataset_path.mkdir(parents=True, exist_ok=True)

        # Process object groups
        for group in dataset_create.object_groups:
            group_metadata, group_files, paths = self._process_object_group_for_upload(
                group, dataset_path)
            files.extend(group_files)
            dataset_create_api.object_groups.append(group_metadata)
            object_group_save_paths.extend(paths)

        # Process variable_groups
        for group in dataset_create.variable_groups:
            group_metadata, path = self._process_variable_group_for_upload(
                group, dataset_path)
            dataset_create_api.variable_groups.append(group_metadata)
            variable_group_save_paths.append(path)

        dataset_from_api = await post_dataset(self.client, files, dataset_create_api)

        return dataset_from_api, object_group_save_paths, variable_group_save_paths

    def _process_object_group_for_upload(self,
                                         group: ObjectGroupCreateWithRawData,
                                         dataset_path: Path
                                         ) -> Tuple[Union[TimeSeriesObjectGroupCreate, TimeSeriesAggregationObjectGroupCreate], List[FileInput], List[Tuple[Path, pd.DataFrame]]]:
        files = []
        group_save_path = dataset_path / str(uuid.uuid4())
        group_save_path.mkdir(parents=True, exist_ok=True)

        group_save_paths: List[Tuple[Path, pd.DataFrame]] = []

        # Note that we only append the metadata files and not the raw data, since we keep the raw data here at the project server
        if group.structure_type == TIME_SERIES_STRUCTURE.first_level_id:

            time_series_save_path = group_save_path / \
                f"{TIME_SERIES_DATA_SECOND_LEVEL_ID}.parquet"
            group_save_paths.append(
                (time_series_save_path, group.data.time_series_data))

            metadata_dataframes = []

            if group.data.entity_metadata is not None and not group.data.entity_metadata.empty:
                buffer = BytesIO()
                group.data.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet"
                files.append(FileInput(
                    field_name="files",
                    filename=filename,
                    file_data=buffer.getvalue(),
                    content_type="application/octet-stream"
                ))

                metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=ENTITY_METADATA_SECOND_LEVEL_ID
                    )
                )
                group_save_paths.append(
                    (group_save_path / filename, group.data.entity_metadata))

            if group.data.feature_information is not None and not group.data.feature_information.empty:
                buffer = BytesIO()
                group.data.feature_information.to_parquet(
                    buffer, index=True)
                buffer.seek(0)
                filename = f"{FEATURE_INFORMATION_SECOND_LEVEL_ID}.parquet"
                files.append(FileInput(
                    field_name="files",
                    filename=filename,
                    file_data=buffer.getvalue(),
                    content_type="application/octet-stream"
                ))

                metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=FEATURE_INFORMATION_SECOND_LEVEL_ID
                    )
                )

                group_save_paths.append(
                    (group_save_path / filename, group.data.feature_information))

            ts_schema, ts_head = _get_df_schema_and_head(
                group.data.time_series_data)
            em_schema, em_head = _get_df_schema_and_head(
                group.data.entity_metadata)
            fi_schema, fi_head = _get_df_schema_and_head(
                group.data.feature_information)

            object_group_create = TimeSeriesObjectGroupCreate(
                name=group.name,
                entity_id_name=group.entity_id_name,
                description=group.description,
                structure_type=group.structure_type,
                save_path=str(group_save_path),
                metadata_dataframes=metadata_dataframes,
                time_series_df_schema=ts_schema,
                time_series_df_head=ts_head,
                entity_metadata_df_schema=em_schema,
                entity_metadata_df_head=em_head,
                feature_information_df_schema=fi_schema,
                feature_information_df_head=fi_head
            )

        elif group.structure_type == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id:

            time_series_aggregation_outputs_save_path = group_save_path / \
                f"{TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID}.parquet"
            group_save_paths.append(
                (time_series_aggregation_outputs_save_path, group.data.time_series_aggregation_outputs))

            metadata_dataframes = []

            if group.data.time_series_aggregation_inputs is not None and not group.data.time_series_aggregation_inputs.empty:
                buffer = BytesIO()
                group.data.time_series_aggregation_inputs.to_parquet(
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

                metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID
                    )
                )
                group_save_paths.append(
                    (group_save_path / filename, group.data.time_series_aggregation_inputs))

            if group.data.entity_metadata is not None and not group.data.entity_metadata.empty:
                buffer = BytesIO()
                group.data.entity_metadata.to_parquet(buffer, index=True)
                buffer.seek(0)
                filename = f"{ENTITY_METADATA_SECOND_LEVEL_ID}.parquet"
                files.append(
                    FileInput(
                        field_name="files",
                        filename=filename,
                        file_data=buffer.getvalue(),
                        content_type="application/octet-stream"
                    ))

                metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=ENTITY_METADATA_SECOND_LEVEL_ID
                    )
                )

                group_save_paths.append(
                    (group_save_path / filename, group.data.entity_metadata))

            if group.data.feature_information is not None and not group.data.feature_information.empty:
                buffer = BytesIO()
                group.data.feature_information.to_parquet(
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

                metadata_dataframes.append(
                    MetadataDataframe(
                        filename=filename,
                        second_level_id=FEATURE_INFORMATION_SECOND_LEVEL_ID
                    )
                )

                group_save_paths.append(
                    (group_save_path / filename, group.data.feature_information))

            ts_agg_outputs_schema, ts_agg_outputs_head = _get_df_schema_and_head(
                group.data.time_series_aggregation_outputs)
            ts_agg_inputs_schema, ts_agg_inputs_head = _get_df_schema_and_head(
                group.data.time_series_aggregation_inputs)
            em_schema, em_head = _get_df_schema_and_head(
                group.data.entity_metadata)
            fi_schema, fi_head = _get_df_schema_and_head(
                group.data.feature_information)

            object_group_create = TimeSeriesAggregationObjectGroupCreate(
                name=group.name,
                entity_id_name=group.entity_id_name,
                description=group.description,
                structure_type=group.structure_type,
                save_path=str(group_save_path),
                metadata_dataframes=metadata_dataframes,
                time_series_aggregation_outputs_df_schema=ts_agg_outputs_schema,
                time_series_aggregation_outputs_df_head=ts_agg_outputs_head,
                time_series_aggregation_inputs_df_schema=ts_agg_inputs_schema,
                time_series_aggregation_inputs_df_head=ts_agg_inputs_head,
                entity_metadata_df_schema=em_schema,
                entity_metadata_df_head=em_head,
                feature_information_df_schema=fi_schema,
                feature_information_df_head=fi_head
            )

        return object_group_create, files, group_save_paths

    def _process_variable_group_for_upload(self, group: VariableGroupCreateWithRawData, dataset_path: Path) -> Tuple[VariableGroupCreate, Tuple[Path, dict]]:
        group_save_path = dataset_path / f"variable_group_{uuid.uuid4()}.json"
        data = self._make_output_variables_serializable(group.data)

        variable_group_create = VariableGroupCreate(
            name=group.name,
            description=group.description,
            save_path=str(group_save_path),
            group_schema=group.group_schema
        )

        return variable_group_create, (group_save_path, data)

    def _make_output_variables_serializable(self, output_variables: dict | object) -> dict:

        if not isinstance(output_variables, dict):
            output_variables = asdict(output_variables)

        serializable = {}
        for key, value in output_variables.items():
            if isinstance(value, dict):
                serializable[key] = self._make_output_variables_serializable(
                    value)
            elif isinstance(value, pd.Timestamp):
                serializable[key] = value.isoformat()
            elif isinstance(value, torch.Tensor):
                if value.numel() == 1:
                    serializable[key] = value.item()
                else:
                    serializable[key] = value.tolist()
            elif isinstance(value, np.ndarray):
                if value.size == 1:
                    serializable[key] = value.item()
                else:
                    serializable[key] = value.tolist()
            elif isinstance(value, (np.floating, np.integer)):
                serializable[key] = value.item()
            elif isinstance(value, list):
                serializable[key] = [
                    self._make_single_value_serializable(item)
                    for item in value
                ]
            else:
                serializable[key] = value
        return serializable

    def _make_single_value_serializable(self, value):
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        elif isinstance(value, (np.floating, np.integer)):
            return value.item()
        elif isinstance(value, dict):
            return self._make_output_variables_serializable(value)
        else:
            return value

    async def _read_structure(self, group_path: Path, structure_type: str) -> Union[TimeSeriesStructure, TimeSeriesAggregationStructure]:
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
