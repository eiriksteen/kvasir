import uuid
import pandas as pd
from typing import List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import insert, select, and_
from fastapi import UploadFile, HTTPException
from synesis_api.modules.data_objects.models import (
    dataset,
    time_series,
    time_series_aggregation,
    object_group,
    data_object,
    feature,
    feature_in_group,
    time_series_aggregation_input,
)
from synesis_api.modules.data_objects.schema import (
    DatasetCreate,
    DatasetInDB,
    ObjectGroupInDB,
    ObjectGroupWithFeatures,
    DataObjectInDB,
    TimeSeriesInDB,
    TimeSeriesAggregationInDB,
    FeatureInDB,
    FeatureInGroupInDB,
    FeatureWithSource,
    TimeSeriesAggregationInputInDB,
    DatasetWithObjectGroups,
    TimeSeriesFull,
    TimeSeriesAggregationFull,
    ObjectGroupWithObjectList,
    ObjectGroupsWithListsInDataset,
)
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_data_structures.time_series.serialization import deserialize_parquet_to_dataframes
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_DATA_SECOND_LEVEL_ID,
    TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID,
    FEATURE_INFORMATION_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID,
    TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID
)
from synesis_api.storage.local import save_dataframe_to_local_storage
from synesis_api.utils.time_series_utils import determine_sampling_frequency, determine_timezone


async def create_features(
    names: List[str],
    units: List[str],
    descriptions: List[str],
    types: List[str],
    subtypes: List[str],
    scales: List[str],
) -> List[FeatureInDB]:

    features_records = [FeatureInDB(
        name=name,
        unit=unit,
        description=description,
        type=type,
        subtype=subtype,
        scale=scale,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ) for name, unit, description, type, subtype, scale in zip(names, units, descriptions, types, subtypes, scales)]

    # Check if features already exist
    existing_features_query = select(feature).where(
        feature.c.name.in_(names)
    )
    existing_features_result = await fetch_all(existing_features_query)
    existing_feature_names = [feature["name"]
                              for feature in existing_features_result]

    new_features = [
        feature for feature in features_records if feature.name not in existing_feature_names]

    if len(new_features) > 0:
        new_features_dump = [feature.model_dump() for feature in new_features]
        await execute(insert(feature).values(new_features_dump), commit_after=True)

    return new_features


async def create_dataset(
        files: list[UploadFile],
        dataset_create: DatasetCreate,
        user_id: uuid.UUID
) -> DatasetInDB:
    """Create a new dataset - placeholder function"""

    # Create dataset
    dataset_record = DatasetInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=dataset_create.name,
        description=dataset_create.description,
        modality=dataset_create.modality,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(dataset).values(dataset_record.model_dump()), commit_after=True)

    for (groups, role) in zip(
        ([dataset_create.primary_object_group],
         dataset_create.annotated_object_groups,
         dataset_create.derived_object_groups),
        ["primary", "annotated", "derived"]
    ):
        for group in groups:
            object_group_record = ObjectGroupInDB(
                id=uuid.uuid4(),
                dataset_id=dataset_record.id,
                name=group.name,
                original_id_name=group.entity_id_name,
                description=group.description,
                role=role,
                structure_type=group.structure_type,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            await execute(insert(object_group).values(object_group_record.model_dump()), commit_after=True)

            # To create the data objects, we must read and deserialize the parquet files from the uploaded file buffers
            parquet_dict = {}
            for dataframe_create in group.dataframes:
                matching_file = None
                for file in files:
                    if file.filename == dataframe_create.filename:
                        matching_file = file
                        break

                if matching_file is None:
                    raise RuntimeError(
                        f"File {dataframe_create.filename} not found in uploaded files"
                    )

                file_content = await matching_file.read()
                parquet_dict[dataframe_create.structure_type] = file_content

            dataframes = deserialize_parquet_to_dataframes(
                parquet_dict,
                group.structure_type
            )

            # Check what data structures are present
            has_feature_information = FEATURE_INFORMATION_SECOND_LEVEL_ID in dataframes
            is_time_series_structure = TIME_SERIES_DATA_SECOND_LEVEL_ID in dataframes
            is_time_series_aggregation_structure = TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID in dataframes

            if has_feature_information:
                features_info = dataframes[FEATURE_INFORMATION_SECOND_LEVEL_ID].reset_index(
                )

                await create_features(
                    names=[record["name"]
                           for record in features_info.to_dict(orient="records")],
                    units=[record["unit"]
                           for record in features_info.to_dict(orient="records")],
                    descriptions=[record["description"]
                                  for record in features_info.to_dict(orient="records")],
                    types=[record["type"]
                           for record in features_info.to_dict(orient="records")],
                    subtypes=[record["subtype"]
                              for record in features_info.to_dict(orient="records")],
                    scales=[record["scale"]
                            for record in features_info.to_dict(orient="records")],
                )

                feature_in_group_dumps = []
                for record in features_info.to_dict(orient="records"):
                    feature_in_group_dumps.append(FeatureInGroupInDB(
                        group_id=object_group_record.id,
                        feature_name=record["name"],
                        source=record['source'],
                        category_id=record['category_id'] if 'category_id' in record else None,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ).model_dump())

                await execute(insert(feature_in_group).values(feature_in_group_dumps), commit_after=True)

            original_entity_id_to_generated_id = {}
            if is_time_series_structure:
                raw_data_second_level_structure_id = TIME_SERIES_DATA_SECOND_LEVEL_ID
                raw_data: pd.DataFrame = dataframes[raw_data_second_level_structure_id]
                metadata: pd.DataFrame = dataframes[
                    TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID] if TIME_SERIES_ENTITY_METADATA_SECOND_LEVEL_ID in dataframes else None

                # Create the time series objects
                for original_entity_id in raw_data.index.get_level_values(0).unique():
                    series: pd.DataFrame = raw_data.loc[original_entity_id]
                    original_id_name = raw_data.index.names[0]
                    original_id = original_entity_id

                    object_record = DataObjectInDB(
                        id=uuid.uuid4(),
                        original_id=str(original_id),
                        name=f"{original_id_name} {original_id}",
                        description=None,
                        group_id=object_group_record.id,
                        additional_variables=metadata.loc[original_entity_id].to_dict(
                        ) if metadata is not None else None,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )

                    await execute(insert(data_object).values(object_record.model_dump()), commit_after=True)

                    # Determine sampling frequency and timezone from the series timestamps
                    timestamps = series.index.tolist()
                    sampling_freq = determine_sampling_frequency(timestamps)
                    tz = determine_timezone(timestamps)

                    # Apply timezone to start and end timestamps
                    start_timestamp: datetime = series.index[0]
                    end_timestamp: datetime = series.index[-1]

                    if start_timestamp.tzinfo is None:
                        start_timestamp = start_timestamp.replace(
                            tzinfo=ZoneInfo(tz))
                    if end_timestamp.tzinfo is None:
                        end_timestamp = end_timestamp.replace(
                            tzinfo=ZoneInfo(tz))

                    time_series_record = TimeSeriesInDB(
                        id=object_record.id,
                        num_timestamps=len(series),
                        start_timestamp=start_timestamp,
                        end_timestamp=end_timestamp,
                        sampling_frequency=sampling_freq,
                        timezone=tz
                    )

                    original_entity_id_to_generated_id[original_entity_id] = time_series_record.id

                    await execute(insert(time_series).values(time_series_record.model_dump()), commit_after=True)

            elif is_time_series_aggregation_structure:
                raw_data_second_level_structure_id = TIME_SERIES_AGGREGATION_OUTPUTS_SECOND_LEVEL_ID
                raw_data: pd.DataFrame = dataframes[raw_data_second_level_structure_id]
                input_data: pd.DataFrame = dataframes[
                    TIME_SERIES_AGGREGATION_INPUTS_SECOND_LEVEL_ID]
                metadata: pd.DataFrame = dataframes[
                    TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID] if TIME_SERIES_AGGREGATION_METADATA_SECOND_LEVEL_ID in dataframes else None

                for aggregation_id in raw_data.index:
                    aggregation_output: pd.DataFrame = raw_data.loc[aggregation_id]
                    aggregation_input: pd.DataFrame = input_data.loc[aggregation_id]

                    original_id_name = aggregation_output.index.name
                    original_id = aggregation_id

                    object_record = DataObjectInDB(
                        id=uuid.uuid4(),
                        name=f"{original_id_name} {original_id}",
                        original_id=original_id,
                        description=None,
                        group_id=object_group_record.id,
                        additional_variables=metadata.loc[
                            aggregation_id].to_dict() if metadata is not None else None,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )

                    await execute(insert(data_object).values(object_record.model_dump()), commit_after=True)

                    # Determine if this is a multi-series computation based on the number of unique time series in the input
                    unique_time_series_ids = aggregation_input['time_series_id'].unique(
                    )
                    is_multi_series_computation = len(
                        unique_time_series_ids) > 1

                    time_series_aggregation_record = TimeSeriesAggregationInDB(
                        id=object_record.id,
                        is_multi_series_computation=is_multi_series_computation,
                    )

                    await execute(insert(time_series_aggregation).values(time_series_aggregation_record.model_dump()), commit_after=True)

                    time_series_aggregation_input_dumps = [TimeSeriesAggregationInputInDB(id=uuid.uuid4(),
                                                                                          aggregation_id=object_record.id,
                                                                                          input_feature_name=record[
                                                                                              "input_feature_name"],
                                                                                          start_timestamp=record[
                                                                                              "start_timestamp"],
                                                                                          end_timestamp=record["end_timestamp"],
                                                                                          time_series_id=original_entity_id_to_generated_id[
                                                                                              record["time_series_id"]],
                                                                                          created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)).model_dump()
                                                           for record in aggregation_input.to_dict(orient="records")]

                    await execute(insert(time_series_aggregation_input).values(time_series_aggregation_input_dumps), commit_after=True)

            else:
                raise ValueError(
                    f"Data structure not supported: {raw_data_second_level_structure_id}")

            save_dataframe_to_local_storage(
                user_id,
                dataset_record.id,
                object_group_record.id,
                raw_data,
                raw_data_second_level_structure_id
            )

        return dataset_record


async def delete_dataset(dataset_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Delete a dataset - placeholder function"""
    # TODO: Implement dataset deletion
    raise NotImplementedError("Dataset deletion not yet implemented")


async def get_user_dataset(
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
) -> DatasetWithObjectGroups:
    """Get a dataset for a user"""

    # Get the base dataset
    dataset_query = select(dataset).where(
        and_(
            dataset.c.id == dataset_id,
            dataset.c.user_id == user_id
        )
    )
    dataset_result = await fetch_one(dataset_query)

    if not dataset_result:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset_obj = DatasetInDB(**dataset_result)

    # Get object groups for this dataset
    object_groups_query = select(object_group).where(
        object_group.c.dataset_id == dataset_id
    )
    object_groups_result = await fetch_all(object_groups_query)

    # Separate object groups by role
    primary_object_group = None
    annotated_object_groups = []
    computed_object_groups = []

    for group_result in object_groups_result:
        group_obj = ObjectGroupInDB(**group_result)
        if group_obj.role == "primary":
            primary_object_group = group_obj
        elif group_obj.role == "annotated":
            annotated_object_groups.append(group_obj)
        elif group_obj.role == "derived":
            computed_object_groups.append(group_obj)

    if not primary_object_group:
        raise HTTPException(
            status_code=400, detail="Dataset must have a primary object group")

    # Create base result

    # Get features for each group
    primary_with_features = await _add_features_to_object_groups(primary_object_group)
    annotated_with_features = [await _add_features_to_object_groups(group) for group in annotated_object_groups]
    computed_with_features = [await _add_features_to_object_groups(group) for group in computed_object_groups]

    result = DatasetWithObjectGroups(
        **dataset_obj.model_dump(),
        primary_object_group=primary_with_features,
        annotated_object_groups=annotated_with_features,
        computed_object_groups=computed_with_features
    )

    return result


async def get_user_datasets(
        user_id: uuid.UUID,
) -> List[DatasetWithObjectGroups]:
    """Get all datasets for a user"""

    # Get all datasets for the user
    datasets_query = select(dataset).where(dataset.c.user_id == user_id)
    datasets_result = await fetch_all(datasets_query)

    if not datasets_result:
        return []

    # Get all object groups for these datasets
    dataset_ids = [d["id"] for d in datasets_result]
    object_groups_query = select(object_group).where(
        object_group.c.dataset_id.in_(dataset_ids)
    )
    object_groups_result = await fetch_all(object_groups_query)

    # Group object groups by dataset_id
    object_groups = [ObjectGroupInDB(**group)
                     for group in object_groups_result]
    object_groups_with_features = await _add_features_to_object_groups(object_groups)

    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)
        primary_object_group = [
            group for group in object_groups_with_features if group.dataset_id == dataset_obj.id and group.role == "primary"][0]
        annotated_object_groups = [
            group for group in object_groups_with_features if group.dataset_id == dataset_obj.id and group.role == "annotated"]
        computed_object_groups = [
            group for group in object_groups_with_features if group.dataset_id == dataset_obj.id and group.role == "derived"]

        result_records.append(DatasetWithObjectGroups(
            **dataset_obj.model_dump(),
            primary_object_group=primary_object_group,
            annotated_object_groups=annotated_object_groups,
            computed_object_groups=computed_object_groups
        ))

    return result_records


async def get_user_datasets_by_ids(
        user_id: uuid.UUID,
        dataset_ids: List[uuid.UUID] = [],
) -> List[DatasetWithObjectGroups]:
    """Get specific datasets for a user by IDs"""

    if not dataset_ids:
        return []

    # Get specific datasets for the user
    datasets_query = select(dataset).where(
        and_(
            dataset.c.user_id == user_id,
            dataset.c.id.in_(dataset_ids)
        )
    )
    datasets_result = await fetch_all(datasets_query)

    if not datasets_result:
        return []

    # Get all object groups for these datasets
    object_groups_query = select(object_group).where(
        object_group.c.dataset_id.in_(dataset_ids)
    )
    object_groups_result = await fetch_all(object_groups_query)

    # Group object groups by dataset_id
    object_groups_by_dataset = {}
    for group_result in object_groups_result:
        group_obj = ObjectGroupInDB(**group_result)
        if group_obj.dataset_id not in object_groups_by_dataset:
            object_groups_by_dataset[group_obj.dataset_id] = []
        object_groups_by_dataset[group_obj.dataset_id].append(group_obj)

    # Build result for each dataset
    result_datasets = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)
        dataset_id = dataset_obj.id

        # Get object groups for this dataset
        dataset_groups = object_groups_by_dataset.get(dataset_id, [])

        # Separate object groups by role
        primary_object_group = None
        annotated_object_groups = []
        computed_object_groups = []

        for group in dataset_groups:
            if group.role == "primary":
                primary_object_group = group
            elif group.role == "annotated":
                annotated_object_groups.append(group)
            elif group.role == "derived":
                computed_object_groups.append(group)

        if primary_object_group:
            # Get features for each group
            primary_with_features = (await _add_features_to_object_groups([primary_object_group]))[0]
            annotated_with_features = await _add_features_to_object_groups(annotated_object_groups)
            computed_with_features = await _add_features_to_object_groups(computed_object_groups)

            dataset_with_objects = DatasetWithObjectGroups(
                **dataset_obj.model_dump(),
                primary_object_group=primary_with_features,
                annotated_object_groups=annotated_with_features,
                computed_object_groups=computed_with_features,
            )

            result_datasets.append(dataset_with_objects)

    return result_datasets


async def get_object_groups(dataset_id: uuid.UUID) -> ObjectGroupsWithListsInDataset:
    """Get all object groups in a dataset"""

    object_group_query = select(object_group).where(
        object_group.c.dataset_id == dataset_id)
    object_groups_result = await fetch_all(object_group_query)

    object_groups = [ObjectGroupInDB(**group)
                     for group in object_groups_result]

    object_groups_with_features = await _add_features_to_object_groups(object_groups)
    object_groups_with_lists = await _add_object_lists_to_object_groups(object_groups_with_features)

    primary_object_group = [
        g for g in object_groups_with_lists if g.role == "primary"][0]
    annotated_object_groups = [
        g for g in object_groups_with_lists if g.role == "annotated"]
    computed_object_groups = [
        g for g in object_groups_with_lists if g.role == "derived"]

    return ObjectGroupsWithListsInDataset(
        dataset_id=dataset_id,
        primary_object_group=primary_object_group,
        annotated_object_groups=annotated_object_groups,
        computed_object_groups=computed_object_groups
    )


async def _add_object_lists_to_object_groups(groups: List[ObjectGroupWithFeatures]) -> List[ObjectGroupWithObjectList]:
    """Helper function to get an object group with its objects"""

    time_series_group_ids = [
        group.id for group in groups if group.structure_type == "time_series"]
    time_series_aggregation_group_ids = [
        group.id for group in groups if group.structure_type == "time_series_aggregation"]

    # Get all data objects in this group
    objects_query = select(data_object).where(
        data_object.c.group_id.in_([group.id for group in groups]))
    objects_result = await fetch_all(objects_query)

    time_series_ids = [
        obj["id"] for obj in objects_result if obj["group_id"] in time_series_group_ids]
    time_series_aggregation_ids = [
        obj["id"] for obj in objects_result if obj["group_id"] in time_series_aggregation_group_ids]

    time_series_objects = await fetch_all(select(time_series).where(
        time_series.c.id.in_(time_series_ids)))
    time_series_aggregation_objects = await fetch_all(select(time_series_aggregation).where(
        time_series_aggregation.c.id.in_(time_series_aggregation_ids)))

    result_records = []
    for group in groups:
        obj_ids = [obj["id"]
                   for obj in objects_result if obj["group_id"] == group.id]
        if group.structure_type == "time_series":
            group_objects = [TimeSeriesFull(
                id=ts_obj["id"],
                name=data_obj["name"],
                description=data_obj["description"],
                original_id=data_obj["original_id"],
                additional_variables=data_obj["additional_variables"],
                created_at=data_obj["created_at"],
                updated_at=data_obj["updated_at"],
                num_timestamps=ts_obj["num_timestamps"],
                start_timestamp=ts_obj["start_timestamp"],
                end_timestamp=ts_obj["end_timestamp"],
                sampling_frequency=ts_obj["sampling_frequency"],
                timezone=ts_obj["timezone"],
            ) for data_obj, ts_obj in zip(objects_result, time_series_objects) if ts_obj["id"] in obj_ids]
        elif group.structure_type == "time_series_aggregation":
            group_objects = [TimeSeriesAggregationFull(
                id=ts_obj["id"],
                name=data_obj["name"],
                description=data_obj["description"],
                original_id=data_obj["original_id"],
                additional_variables=data_obj["additional_variables"],
                created_at=data_obj["created_at"],
                updated_at=data_obj["updated_at"],
                is_multi_series_computation=ts_obj["is_multi_series_computation"],
            ) for data_obj, ts_obj in zip(objects_result, time_series_aggregation_objects) if ts_obj["id"] in obj_ids]

        result_records.append(ObjectGroupWithObjectList(
            **group.model_dump(), objects=group_objects))

    return result_records


async def _add_features_to_object_groups(groups: List[ObjectGroupInDB]) -> List[ObjectGroupWithFeatures]:
    """Helper function to get an object group with its features"""

    # Get features for this group by joining feature and feature_in_group tables
    features_query = select(
        feature.c.name,
        feature.c.unit,
        feature.c.description,
        feature.c.type,
        feature.c.subtype,
        feature.c.scale,
        feature_in_group.c.source,
        feature_in_group.c.category_id,
        feature_in_group.c.group_id,
        feature.c.created_at,
        feature.c.updated_at
    ).join(
        feature_in_group,
        feature.c.name == feature_in_group.c.feature_name
    ).where(
        feature_in_group.c.group_id.in_([group.id for group in groups])
    )
    features_result = await fetch_all(features_query)

    result_records = []
    for group in groups:
        group_features = [FeatureWithSource(
            **feature) for feature in features_result if feature["group_id"] == group.id]
        result_records.append(ObjectGroupWithFeatures(
            **group.model_dump(), features=group_features))

    return result_records


async def entity_metadata_to_df(entity_ids: List[str]) -> pd.DataFrame:
    # TODO: Implement entity metadata to dataframe
    pass


async def feature_metadata_to_df(feature_names: Optional[List[str]] = None, group_id: Optional[uuid.UUID] = None) -> pd.DataFrame:

    assert feature_names is not None or group_id is not None, "Either feature_names or group_id must be provided"

    if feature_names is not None:
        feature_query = select(feature).where(
            feature.c.name.in_(feature_names))
    elif group_id is not None:
        feature_query = select(feature).join(feature_in_group).where(
            feature_in_group.c.group_id == group_id,
            feature.c.name == feature_in_group.c.feature_name
        )

    feature_result = await fetch_all(feature_query)
    return pd.DataFrame(feature_result).set_index("name")
