import uuid
import pytz
from typing import List, Optional, Dict, Union
from datetime import datetime, timezone
from sqlalchemy import insert, select, update
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
    variable_group,
    dataset_from_data_source,
    dataset_from_dataset,
    dataset_from_pipeline,
    time_series_object_group,
    time_series_aggregation_object_group,
    aggregation_object
)
from synesis_schemas.main_server import (
    FeatureCreate,
    DatasetCreate,
    DatasetInDB,
    ObjectGroupInDB,
    ObjectGroupWithObjects,
    DataObjectInDB,
    TimeSeriesInDB,
    TimeSeriesAggregationInDB,
    FeatureInDB,
    FeatureInGroupInDB,
    FeatureWithSource,
    TimeSeriesAggregationInputInDB,
    Dataset,
    DataObject,
    ObjectGroupWithObjects,
    VariableGroupInDB,
    DatasetSources,
    DatasetFromDataSourceInDB,
    DatasetFromDatasetInDB,
    DatasetFromPipelineInDB,
    TimeSeriesObjectGroupInDB,
    TimeSeriesAggregationObjectGroupInDB,
    ObjectGroup,
    DataObjectWithParentGroup,
    AggregationObjectWithRawData,
    AggregationObjectInDB,
    AggregationObjectCreate,
    AggregationObjectUpdate
)
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.project.service import get_dataset_ids_in_project

from synesis_data_structures.time_series.serialization import deserialize_parquet_to_dataframes
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_STRUCTURE,
    TIME_SERIES_AGGREGATION_STRUCTURE
)


async def create_features(features: List[FeatureCreate]) -> List[FeatureInDB]:

    features_records = [FeatureInDB(
        name=feature.name,
        unit=feature.unit,
        description=feature.description,
        type=feature.type,
        subtype=feature.subtype,
        scale=feature.scale,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ) for feature in features]

    # Check if features already exist
    existing_features_query = select(feature).where(
        feature.c.name.in_([feature.name for feature in features_records])
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
        user_id: uuid.UUID) -> Dataset:

    # Create dataset
    dataset_record = DatasetInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=dataset_create.name,
        description=dataset_create.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(dataset).values(dataset_record.model_dump()), commit_after=True)

    # Create the sources
    from_data_source_records, from_dataset_records, from_pipeline_records = [], [], []
    for source in list(set(dataset_create.sources.data_source_ids)):
        from_data_source_records.append(DatasetFromDataSourceInDB(
            dataset_id=dataset_record.id,
            data_source_id=source).model_dump())
    for source in list(set(dataset_create.sources.dataset_ids)):
        from_dataset_records.append(DatasetFromDatasetInDB(
            dataset_id=dataset_record.id,
            source_dataset_id=source).model_dump())
    for source in list(set(dataset_create.sources.pipeline_ids)):
        from_pipeline_records.append(DatasetFromPipelineInDB(
            dataset_id=dataset_record.id,
            pipeline_id=source).model_dump())

    if len(from_data_source_records) > 0:
        await execute(insert(dataset_from_data_source).values(from_data_source_records), commit_after=True)
    if len(from_dataset_records) > 0:
        await execute(insert(dataset_from_dataset).values(from_dataset_records), commit_after=True)
    if len(from_pipeline_records) > 0:
        await execute(insert(dataset_from_pipeline).values(from_pipeline_records), commit_after=True)

    # Variables to collect object groups for the response
    object_group_records: List[ObjectGroupInDB] = []
    time_series_object_group_records: List[TimeSeriesObjectGroupInDB] = []
    time_series_aggregation_object_group_records: List[TimeSeriesAggregationObjectGroupInDB] = [
    ]
    for group in dataset_create.object_groups:
        object_group_record = ObjectGroupInDB(
            id=uuid.uuid4(),
            dataset_id=dataset_record.id,
            name=group.name,
            original_id_name=group.entity_id_name,
            description=group.description,
            structure_type=group.structure_type,
            save_path=group.save_path,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(object_group).values(object_group_record.model_dump()), commit_after=True)

        object_group_records.append(object_group_record)

        if group.structure_type == TIME_SERIES_STRUCTURE.first_level_id:
            time_series_object_group_record = TimeSeriesObjectGroupInDB(
                id=object_group_record.id,
                time_series_df_schema=group.time_series_df_schema,
                time_series_df_head=group.time_series_df_head,
                entity_metadata_df_schema=group.entity_metadata_df_schema,
                entity_metadata_df_head=group.entity_metadata_df_head,
                feature_information_df_schema=group.feature_information_df_schema,
                feature_information_df_head=group.feature_information_df_head,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            await execute(insert(time_series_object_group).values(time_series_object_group_record.model_dump()), commit_after=True)

            time_series_object_group_records.append(
                time_series_object_group_record)
        elif group.structure_type == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id:
            time_series_aggregation_object_group_record = TimeSeriesAggregationObjectGroupInDB(
                id=object_group_record.id,
                time_series_aggregation_outputs_df_schema=group.time_series_aggregation_outputs_df_schema,
                time_series_aggregation_outputs_df_head=group.time_series_aggregation_outputs_df_head,
                time_series_aggregation_inputs_df_schema=group.time_series_aggregation_inputs_df_schema,
                time_series_aggregation_inputs_df_head=group.time_series_aggregation_inputs_df_head,
                entity_metadata_df_schema=group.entity_metadata_df_schema,
                entity_metadata_df_head=group.entity_metadata_df_head,
                feature_information_df_schema=group.feature_information_df_schema,
                feature_information_df_head=group.feature_information_df_head,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            await execute(insert(time_series_aggregation_object_group).values(time_series_aggregation_object_group_record.model_dump()), commit_after=True)

            time_series_aggregation_object_group_records.append(
                time_series_aggregation_object_group_record)
        else:
            raise ValueError(
                f"Data structure not supported: {group.structure_type}")
        # To create the data objects, we must read and deserialize the parquet files from the uploaded file buffers
        parquet_dict = {}
        for dataframe_create in group.metadata_dataframes:
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
            parquet_dict[dataframe_create.second_level_id] = file_content

        structure = deserialize_parquet_to_dataframes(
            parquet_dict, group.structure_type, only_metadata=True)

        # Check what data structures are present
        is_time_series_structure = group.structure_type == TIME_SERIES_STRUCTURE.first_level_id
        is_time_series_aggregation_structure = group.structure_type == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id

        if structure.feature_information is not None:
            features_info = structure.feature_information.reset_index()
            await create_features(features=[FeatureCreate(**record) for record in features_info.reset_index().to_dict(orient="records")])

            feature_in_group_dumps = []
            for record in features_info.reset_index().to_dict(orient="records"):
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
            metadata = structure.entity_metadata
            fixed_columns = ["num_timestamps", "start_timestamp",
                             "end_timestamp", "sampling_frequency", "timezone"]
            additional_columns = [
                col for col in metadata.columns if col not in fixed_columns]

            fixed_metadata = metadata[fixed_columns]
            additional_metadata = metadata[additional_columns]

            object_records = []
            time_series_records = []

            for entity_id in metadata.index:
                object_record = DataObjectInDB(
                    id=uuid.uuid4(),
                    name=entity_id,
                    structure_type=TIME_SERIES_STRUCTURE.first_level_id,
                    group_id=object_group_record.id,
                    original_id=entity_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    additional_variables=additional_metadata.loc[entity_id].to_dict(
                    )
                )

                object_records.append(object_record.model_dump())

                # Extract timestamp values and make them timezone-aware
                entity_timezone = fixed_metadata.loc[entity_id, 'timezone']
                start_timestamp = _make_timezone_aware(
                    fixed_metadata.loc[entity_id, 'start_timestamp'],
                    entity_timezone
                )
                end_timestamp = _make_timezone_aware(
                    fixed_metadata.loc[entity_id, 'end_timestamp'],
                    entity_timezone
                )

                time_series_record = TimeSeriesInDB(
                    id=object_record.id,
                    num_timestamps=fixed_metadata.loc[entity_id,
                                                      'num_timestamps'],
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    sampling_frequency=fixed_metadata.loc[entity_id,
                                                          'sampling_frequency'],
                    timezone=entity_timezone
                )

                original_entity_id_to_generated_id[entity_id] = time_series_record.id

                time_series_records.append(time_series_record.model_dump())

            await execute(insert(data_object).values(object_records), commit_after=True)
            await execute(insert(time_series).values(time_series_records), commit_after=True)

        elif is_time_series_aggregation_structure:

            metadata = structure.entity_metadata
            fixed_columns = ["is_multi_series_computation"]
            additional_columns = [
                col for col in metadata.columns if col not in fixed_columns]

            fixed_metadata = metadata[fixed_columns]
            additional_metadata = metadata[additional_columns]
            inputs_metadata = structure.time_series_aggregation_inputs

            object_records = []
            agg_records = []
            input_records = []

            for aggregation_id in metadata.index:
                object_record = DataObjectInDB(
                    id=uuid.uuid4(),
                    name=aggregation_id,
                    structure_type=TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id,
                    group_id=object_group_record.id,
                    original_id=aggregation_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    additional_variables=additional_metadata.loc[aggregation_id].to_dict(
                    )
                )

                object_records.append(object_record.model_dump())

                time_series_aggregation_record = TimeSeriesAggregationInDB(
                    id=object_record.id,
                    **fixed_metadata.loc[aggregation_id].to_dict()
                )

                agg_records.append(
                    time_series_aggregation_record.model_dump())

                for agg_input in inputs_metadata.iterrows():
                    time_series_aggregation_input_record = TimeSeriesAggregationInputInDB(
                        id=uuid.uuid4(),
                        time_series_id=original_entity_id_to_generated_id[agg_input["time_series_id"]],
                        aggregation_id=object_record.id,
                        **agg_input.to_dict()
                    )
                    input_records.append(
                        time_series_aggregation_input_record.model_dump())

            await execute(insert(data_object).values(object_records), commit_after=True)
            await execute(insert(time_series_aggregation).values(agg_records), commit_after=True)
            await execute(insert(time_series_aggregation_input).values(input_records), commit_after=True)

        else:
            raise ValueError(
                f"Data structure not supported: {structure}")

    variable_group_records = []
    for variable_group_create in dataset_create.variable_groups:
        variable_group_record = VariableGroupInDB(
            id=uuid.uuid4(),
            dataset_id=dataset_record.id,
            name=variable_group_create.name,
            description=variable_group_create.description,
            save_path=variable_group_create.save_path,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        variable_group_records.append(variable_group_record.model_dump())

    if len(variable_group_records) > 0:
        await execute(insert(variable_group).values(variable_group_records), commit_after=True)

    return await get_user_dataset_by_id(dataset_record.id, user_id)


async def get_user_datasets(
        user_id: uuid.UUID,
        ids: Optional[List[uuid.UUID]] = None,
        max_features: Optional[int] = None
) -> List[Dataset]:
    """Get all datasets for a user"""

    # Get all datasets for the user
    datasets_query = select(dataset).where(dataset.c.user_id == user_id)

    if ids is not None:
        datasets_query = datasets_query.where(dataset.c.id.in_(ids))

    datasets_result = await fetch_all(datasets_query)

    if not datasets_result:
        return []

    # Get all data source, source dataset, and pipeline IDs
    source_ids_query = select(dataset_from_data_source).where(
        dataset_from_data_source.c.dataset_id.in_(
            [d["id"] for d in datasets_result])
    )
    source_ids_result = await fetch_all(source_ids_query)

    source_dataset_ids_query = select(dataset_from_dataset).where(
        dataset_from_dataset.c.dataset_id.in_(
            [d["id"] for d in datasets_result])
    )
    source_dataset_ids_result = await fetch_all(source_dataset_ids_query)

    pipeline_ids_query = select(dataset_from_pipeline).where(
        dataset_from_pipeline.c.dataset_id.in_(
            [d["id"] for d in datasets_result])
    )
    pipeline_ids_result = await fetch_all(pipeline_ids_query)

    # Get all object groups
    dataset_ids = [d["id"] for d in datasets_result]
    object_groups_query = select(object_group).where(
        object_group.c.dataset_id.in_(dataset_ids)
    )
    object_groups_result = await fetch_all(object_groups_query)

    group_ids = [group["id"] for group in object_groups_result]

    time_series_object_groups_query = select(time_series_object_group).where(
        time_series_object_group.c.id.in_(group_ids)
    )
    time_series_object_groups_result = await fetch_all(time_series_object_groups_query)

    time_series_aggregation_object_groups_query = select(time_series_aggregation_object_group).where(
        time_series_aggregation_object_group.c.id.in_(group_ids)
    )
    time_series_aggregation_object_groups_result = await fetch_all(time_series_aggregation_object_groups_query)

    features_per_group = await _get_features_per_group_id(group_ids, max_features=max_features)

    # Get all variable groups
    variable_groups_query = select(variable_group).where(
        variable_group.c.dataset_id.in_(dataset_ids)
    )
    variable_groups_result = await fetch_all(variable_groups_query)

    # Prepare the final records
    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)

        time_series_object_groups = [
            ObjectGroup(
                **group,
                structure_fields=ts_record,
                features=features_per_group[group["id"]]
            )
            for group, ts_record in zip(object_groups_result, time_series_object_groups_result) if group["dataset_id"] == dataset_obj.id
        ]
        time_series_aggregation_object_groups = [
            ObjectGroup(
                **group,
                structure_fields=agg_record,
                features=features_per_group[group["id"]]
            )
            for group, agg_record in zip(object_groups_result, time_series_aggregation_object_groups_result) if group["dataset_id"] == dataset_obj.id
        ]

        all_object_groups = time_series_object_groups + \
            time_series_aggregation_object_groups

        sources = DatasetSources(
            data_source_ids=[rec["data_source_id"]
                             for rec in source_ids_result if rec["dataset_id"] == dataset_obj.id],
            dataset_ids=[rec["source_dataset_id"]
                         for rec in source_dataset_ids_result if rec["dataset_id"] == dataset_obj.id],
            pipeline_ids=[rec["pipeline_id"]
                          for rec in pipeline_ids_result if rec["dataset_id"] == dataset_obj.id]
        )

        variable_groups = [
            VariableGroupInDB(**group) for group in variable_groups_result if group["dataset_id"] == dataset_obj.id]

        record = Dataset(
            **dataset_obj.model_dump(),
            object_groups=all_object_groups,
            variable_groups=variable_groups,
            sources=sources
        )

        result_records.append(record)

    return result_records


async def get_user_dataset_by_id(
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
) -> Dataset:
    """Get a dataset for a user"""

    return (await get_user_datasets(user_id, ids=[dataset_id]))[0]


async def get_project_datasets(user_id: uuid.UUID, project_id: uuid.UUID) -> List[Dataset]:
    dataset_ids = await get_dataset_ids_in_project(project_id)
    return await get_user_datasets(user_id, ids=dataset_ids)


async def get_object_groups(
    dataset_id: Optional[uuid.UUID] = None,
    group_ids: Optional[List[uuid.UUID]] = None,
    include_objects: bool = False
) -> List[Union[ObjectGroupWithObjects, ObjectGroup]]:
    """Get object groups"""

    object_group_query = select(object_group)

    if dataset_id is not None:
        object_group_query = object_group_query.where(
            object_group.c.dataset_id == dataset_id)
    if group_ids is not None:
        object_group_query = object_group_query.where(
            object_group.c.id.in_(group_ids))

    object_groups_result = await fetch_all(object_group_query)
    object_group_ids = [group["id"] for group in object_groups_result]

    time_series_object_groups_query = select(time_series_object_group).where(
        time_series_object_group.c.id.in_(object_group_ids))
    time_series_object_groups_result = await fetch_all(time_series_object_groups_query)
    time_series_aggregation_object_groups_query = select(time_series_aggregation_object_group).where(
        time_series_aggregation_object_group.c.id.in_(object_group_ids))
    time_series_aggregation_object_groups_result = await fetch_all(time_series_aggregation_object_groups_query)

    features_per_group = await _get_features_per_group_id(object_group_ids)

    data_object_records = None
    if include_objects:
        data_object_records = await get_data_objects(group_ids=object_group_ids, include_object_group=False)

    result_records = []
    for group in object_groups_result:
        if group["structure_type"] == TIME_SERIES_STRUCTURE.first_level_id:
            structure_fields = next(
                (ts_group for ts_group in time_series_object_groups_result if ts_group["id"] == group["id"]), None)
        elif group["structure_type"] == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id:
            structure_fields = next(
                (ts_agg_group for ts_agg_group in time_series_aggregation_object_groups_result if ts_agg_group["id"] == group["id"]), None)
        else:
            raise ValueError(
                f"Unknown structure type: {group['structure_type']}")

        if include_objects:
            objects_in_group = [
                obj_rec for obj_rec in data_object_records if obj_rec.group_id == group["id"]]
            result_records.append(ObjectGroupWithObjects(
                **group,
                structure_fields=structure_fields,
                features=features_per_group[group["id"]],
                objects=objects_in_group
            ))
        else:
            result_records.append(ObjectGroup(
                **group,
                structure_fields=structure_fields,
                features=features_per_group[group["id"]]
            ))

    return result_records


async def get_object_group(
        group_id: uuid.UUID,
        include_objects: bool = False,
) -> Union[ObjectGroupWithObjects, ObjectGroup]:
    """Get an object group"""
    return (await get_object_groups(group_ids=[group_id], include_objects=include_objects))[0]


async def get_data_objects(
    object_ids: Optional[List[uuid.UUID]] = None,
    group_ids: Optional[List[uuid.UUID]] = None,
    include_object_group: bool = False
) -> List[Union[DataObjectWithParentGroup, DataObject]]:

    assert object_ids is not None or group_ids is not None, "Either object_ids or group_ids must be provided"

    objects_query = select(data_object)
    if object_ids is not None:
        objects_query = objects_query.where(data_object.c.id.in_(object_ids))
    if group_ids is not None:
        objects_query = objects_query.where(
            data_object.c.group_id.in_(group_ids))

    objects_result = await fetch_all(objects_query)
    object_ids = [obj["id"] for obj in objects_result]

    time_series_objects = await fetch_all(select(time_series).where(time_series.c.id.in_(object_ids)))
    time_series_aggregation_objects = await fetch_all(select(time_series_aggregation).where(time_series_aggregation.c.id.in_(object_ids)))

    result_records = []
    for object_id in object_ids:
        data_object_record = next(DataObjectInDB(**obj)
                                  for obj in objects_result if obj["id"] == object_id)

        time_series_object_record = next((TimeSeriesInDB(
            **obj) for obj in time_series_objects if obj["id"] == object_id), None)

        time_series_aggregation_object_record = next((TimeSeriesAggregationInDB(
            **obj) for obj in time_series_aggregation_objects if obj["id"] == object_id), None)

        assert time_series_object_record is not None or time_series_aggregation_object_record is not None, "Time series object or time series aggregation not found"

        if include_object_group:
            result_records.append(DataObjectWithParentGroup(
                **data_object_record.model_dump(),
                structure_fields=time_series_object_record if time_series_object_record is not None else time_series_aggregation_object_record,
                object_group=await get_object_group(data_object_record.group_id, include_objects=False)
            ))

        else:
            result_records.append(DataObject(
                **data_object_record.model_dump(),
                structure_fields=time_series_object_record if time_series_object_record is not None else time_series_aggregation_object_record,
            ))

    return result_records


async def get_data_object(object_id: uuid.UUID, include_object_group: bool = False) -> Union[DataObjectWithParentGroup, DataObject]:
    return (await get_data_objects(object_ids=[object_id], include_object_group=include_object_group))[0]


async def _get_features_per_group_id(group_ids: List[uuid.UUID], max_features: Optional[int] = None) -> Dict[uuid.UUID, List[FeatureWithSource]]:
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
        feature_in_group.c.group_id.in_(group_ids)
    )

    if max_features:
        features_query = features_query.limit(max_features)

    features_result = await fetch_all(features_query)

    result_dict = {}
    for group_id in group_ids:
        group_features = [FeatureWithSource(
            **feature) for feature in features_result if feature["group_id"] == group_id]
        result_dict[group_id] = group_features

    return result_dict


def _make_timezone_aware(dt: datetime, timezone_str: str) -> datetime:
    """Convert a naive datetime to timezone-aware using the provided timezone string.

    Args:
        dt: The datetime object to convert (may be naive)
        timezone_str: The timezone string (e.g., 'UTC', 'America/New_York')

    Returns:
        Timezone-aware datetime object
    """
    if dt.tzinfo is not None:
        # Already timezone-aware, return as-is
        return dt

    # Convert naive datetime to timezone-aware
    tz = pytz.timezone(timezone_str)
    return tz.localize(dt)
    return result_records


async def create_aggregation_object(aggregation_object_create: AggregationObjectCreate) -> AggregationObjectInDB:
    id = uuid.uuid4()
    aggregation_object_in_db = AggregationObjectInDB(
        id=id,
        name=aggregation_object_create.name,
        description=aggregation_object_create.description,
        analysis_result_id=aggregation_object_create.analysis_result_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await execute(insert(aggregation_object).values(aggregation_object_in_db.model_dump()), commit_after=True)
    return aggregation_object_in_db


async def update_aggregation_object(aggregation_object_id: uuid.UUID, aggregation_object_update: AggregationObjectUpdate) -> AggregationObjectInDB:
    aggregation_object_query = select(aggregation_object).where(
        aggregation_object.c.id == aggregation_object_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    if not aggregation_object_result:
        raise HTTPException(
            status_code=404, detail="Aggregation object not found")
    await execute(update(aggregation_object).where(aggregation_object.c.id == aggregation_object_id).values(aggregation_object_update.model_dump()), commit_after=True)
    return AggregationObjectInDB(**aggregation_object_result)


async def get_aggregation_object(aggregation_object_id: uuid.UUID) -> AggregationObjectInDB:
    aggregation_object_query = select(aggregation_object).where(
        aggregation_object.c.id == aggregation_object_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    return AggregationObjectInDB(**aggregation_object_result)


async def get_aggregation_object_by_analysis_result_id(analysis_result_id: uuid.UUID) -> AggregationObjectInDB:
    aggregation_object_query = select(aggregation_object).where(
        aggregation_object.c.analysis_result_id == analysis_result_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    if not aggregation_object_result:
        raise HTTPException(
            status_code=404, detail="Aggregation object not found")
    return AggregationObjectInDB(**aggregation_object_result)

