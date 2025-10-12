import uuid
import pandas as pd
from typing import List, Optional, Union
from datetime import datetime, timezone
from sqlalchemy import insert, select, and_, update
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
    variable,
    dataset_from_data_source,
    dataset_from_dataset,
    dataset_from_pipeline,
    aggregation_object
)
from synesis_schemas.main_server import (
    FeatureCreate,
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
    DatasetFull,
    DatasetFullWithFeatures,
    TimeSeriesFull,
    TimeSeriesAggregationFull,
    ObjectGroupWithEntitiesAndFeatures,
    VariableGroupInDB,
    VariableInDB,
    VariableGroupFull,
    DatasetSources,
    DatasetFromDataSourceInDB,
    DatasetFromDatasetInDB,
    DatasetFromPipelineInDB,
    AggregationObjectWithRawData, 
    AggregationObjectInDB, 
    AggregationObjectCreate, 
    AggregationObjectUpdate
)
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.modules.project.service import get_dataset_ids_in_project

from synesis_data_structures.time_series.serialization import deserialize_parquet_to_dataframes, serialize_raw_data_for_aggregation_object_for_api
from synesis_data_structures.time_series.definitions import (
    TIME_SERIES_STRUCTURE,
    TIME_SERIES_AGGREGATION_STRUCTURE
)
from synesis_api.utils.time_series_utils import make_timezone_aware

from synesis_api.modules.analysis.service import get_analysis_result_by_id
from synesis_api.modules.data_sources.service import get_data_sources
from synesis_api.utils.file_utils import copy_file_or_directory_to_container, get_data_from_container_from_code
from synesis_api.app_secrets import DATASETS_SAVE_PATH, RAW_FILES_SAVE_DIR
from pathlib import Path


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
        user_id: uuid.UUID) -> DatasetFull:

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
    object_group_records = []
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
            await create_features(features=[FeatureCreate(**record) for record in features_info.to_dict(orient="records")])

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
                start_timestamp = make_timezone_aware(
                    fixed_metadata.loc[entity_id, 'start_timestamp'],
                    entity_timezone
                )
                end_timestamp = make_timezone_aware(
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
    variable_group_full_records = []
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

        variable_records = []
        for variable_create in variable_group_create.variables:
            variable_record = VariableInDB(
                id=uuid.uuid4(),
                variable_group_id=variable_group_record.id,
                name=variable_create.name,
                python_type=variable_create.python_type,
                description=variable_create.description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            variable_records.append(variable_record.model_dump())

        variable_group_full_records.append(VariableGroupFull(
            **variable_group_record.model_dump(),
            variables=variable_records
        ))

    if len(variable_group_records) > 0 and len(variable_records) > 0:
        await execute(insert(variable_group).values(variable_group_records), commit_after=True)
        await execute(insert(variable).values(variable_records), commit_after=True)

    # Return the dataset with object groups
    return DatasetFull(
        **dataset_record.model_dump(),
        object_groups=object_group_records,
        variable_groups=variable_group_full_records,
        sources=dataset_create.sources
    )


async def get_user_datasets(
        user_id: uuid.UUID,
        include_features: bool = False,
        ids: Optional[List[uuid.UUID]] = None,
        max_features: Optional[int] = None,
) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
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

    object_groups = [ObjectGroupInDB(**group)
                     for group in object_groups_result]

    if include_features:
        object_groups = await _add_features_to_object_groups(object_groups, max_features=max_features)

    # Get all variable groups
    variable_groups_query = select(variable_group).where(
        variable_group.c.dataset_id.in_(dataset_ids)
    )
    variable_groups_result = await fetch_all(variable_groups_query)

    variables_query = select(variable).where(
        variable.c.variable_group_id.in_(
            [group["id"] for group in variable_groups_result])
    )
    variables_result = await fetch_all(variables_query)

    variable_groups = [VariableGroupInDB(**group)
                       for group in variable_groups_result]

    variables = [VariableInDB(**variable)
                 for variable in variables_result]

    # Prepare the final records
    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)

        object_groups = [
            group for group in object_groups if group.dataset_id == dataset_obj.id]

        sources = DatasetSources(
            data_source_ids=[rec["data_source_id"]
                             for rec in source_ids_result if rec["dataset_id"] == dataset_obj.id],
            dataset_ids=[rec["source_dataset_id"]
                         for rec in source_dataset_ids_result if rec["dataset_id"] == dataset_obj.id],
            pipeline_ids=[rec["pipeline_id"]
                          for rec in pipeline_ids_result if rec["dataset_id"] == dataset_obj.id]
        )

        variable_groups = [
            group for group in variable_groups if group.dataset_id == dataset_obj.id]

        variables = [variable for variable in variables if variable.variable_group_id in [
            group.id for group in variable_groups]]

        variable_groups_full = [VariableGroupFull(
            **group.model_dump(),
            variables=variables
        ) for group in variable_groups]

        if include_features:
            record = DatasetFullWithFeatures(
                **dataset_obj.model_dump(),
                object_groups=object_groups,
                variable_groups=variable_groups_full,
                sources=sources
            )
        else:
            record = DatasetFull(
                **dataset_obj.model_dump(),
                object_groups=object_groups,
                variable_groups=variable_groups_full,
                sources=sources
            )

        result_records.append(record)

    return result_records


async def get_user_datasets_by_ids(
        user_id: uuid.UUID,
        dataset_ids: List[uuid.UUID] = [],
        max_features: Optional[int] = None,
        include_features: bool = False
) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    """Get specific datasets for a user by IDs"""

    return await get_user_datasets(user_id, ids=dataset_ids, include_features=include_features, max_features=max_features)


async def get_user_dataset_by_id(
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        include_features: bool = False
) -> Union[DatasetFullWithFeatures, DatasetFull]:
    """Get a dataset for a user"""

    return (await get_user_datasets_by_ids(user_id, [dataset_id], include_features=include_features))[0]


async def get_object_groups_in_dataset_with_entities_and_features(dataset_id: uuid.UUID) -> List[ObjectGroupWithEntitiesAndFeatures]:
    """Get all object groups in a dataset"""

    object_group_query = select(object_group).where(
        object_group.c.dataset_id == dataset_id)
    object_groups_result = await fetch_all(object_group_query)

    object_groups = [ObjectGroupInDB(**group)
                     for group in object_groups_result]

    object_groups_with_features = await _add_features_to_object_groups(object_groups)
    object_groups_with_lists = await _add_object_lists_to_object_groups(object_groups_with_features)

    return object_groups_with_lists


async def get_project_datasets(user_id: uuid.UUID, project_id: uuid.UUID, include_features: bool = False) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    dataset_ids = await get_dataset_ids_in_project(project_id)
    return await get_user_datasets_by_ids(user_id, dataset_ids, include_features=include_features)


async def get_user_datasets_by_ids(
        user_id: uuid.UUID,
        dataset_ids: List[uuid.UUID] = [],
        max_features: Optional[int] = None,
        include_features: bool = False
) -> List[Union[DatasetFullWithFeatures, DatasetFull]]:
    """Get specific datasets for a user by IDs"""
    return await get_user_datasets(user_id, ids=dataset_ids, include_features=include_features, max_features=max_features)


async def get_object_group(
        group_id: uuid.UUID,
        include_features: bool = False,
        include_entities: bool = False,
) -> Union[ObjectGroupInDB, ObjectGroupWithFeatures, ObjectGroupWithEntitiesAndFeatures]:
    """Get an object group"""

    object_group_query = select(object_group).where(
        object_group.c.id == group_id)

    object_group_result = await fetch_one(object_group_query)

    object_group_obj = ObjectGroupInDB(**object_group_result)

    if include_features:
        object_group_obj = await _add_features_to_object_groups([object_group_obj])[0]
    if include_entities:
        object_group_obj = await _add_object_lists_to_object_groups([object_group_obj])[0]

    return object_group_obj


async def _add_object_lists_to_object_groups(groups: List[ObjectGroupWithFeatures]) -> List[ObjectGroupWithEntitiesAndFeatures]:
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

        result_records.append(ObjectGroupWithEntitiesAndFeatures(
            **group.model_dump(), objects=group_objects))

    return result_records


async def _add_features_to_object_groups(groups: List[ObjectGroupInDB], max_features: Optional[int] = None) -> List[ObjectGroupWithFeatures]:
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

    if max_features:
        features_query = features_query.limit(max_features)

    features_result = await fetch_all(features_query)

    result_records = []
    for group in groups:
        group_features = [FeatureWithSource(
            **feature) for feature in features_result if feature["group_id"] == group.id]
        result_records.append(ObjectGroupWithFeatures(
            **group.model_dump(), features=group_features))

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
    aggregation_object_query = select(aggregation_object).where(aggregation_object.c.id == aggregation_object_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    if not aggregation_object_result:
        raise HTTPException(status_code=404, detail="Aggregation object not found")
    await execute(update(aggregation_object).where(aggregation_object.c.id == aggregation_object_id).values(aggregation_object_update.model_dump()), commit_after=True)
    return AggregationObjectInDB(**aggregation_object_result)

async def get_aggregation_object(aggregation_object_id: uuid.UUID) -> AggregationObjectInDB:
    aggregation_object_query = select(aggregation_object).where(aggregation_object.c.id == aggregation_object_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    return AggregationObjectInDB(**aggregation_object_result)

async def get_aggregation_object_by_analysis_result_id(analysis_result_id: uuid.UUID) -> AggregationObjectInDB:
    aggregation_object_query = select(aggregation_object).where(aggregation_object.c.analysis_result_id == analysis_result_id)
    aggregation_object_result = await fetch_one(aggregation_object_query)
    if not aggregation_object_result:
        raise HTTPException(status_code=404, detail="Aggregation object not found")
    return AggregationObjectInDB(**aggregation_object_result)



async def get_aggregation_object_payload_data_by_analysis_result_id(
    user_id: uuid.UUID,
    analysis_result_id: uuid.UUID,
) -> AggregationObjectWithRawData:
    aggregation_object_in_db = await get_aggregation_object_by_analysis_result_id(analysis_result_id)

    analysis_result = await get_analysis_result_by_id(analysis_result_id)

    datasets = await get_user_datasets_by_ids(user_id, analysis_result.dataset_ids)
    for idx, dataset in enumerate(datasets):
        file_path = DATASETS_SAVE_PATH / \
            f"{user_id}" / \
            f"{dataset.id}" / \
            f"{dataset.primary_object_group.id}" / \
            f"{dataset.primary_object_group.structure_type}_data.parquet"
        container_save_path = Path("/tmp") / f"dataset_{idx}.parquet"

        out, err = await copy_file_or_directory_to_container(file_path, container_save_path)

    data_sources = await get_data_sources(analysis_result.data_source_ids)
    for idx, data_source in enumerate(data_sources):
        file_path = RAW_FILES_SAVE_DIR / \
            f"{user_id}" / \
            f"{data_source.id}" / \
            f"{data_source.name}"
        print("copying data source:", file_path)
        container_save_path = Path("/tmp") / f"data_source_{idx}.csv"
        out, err = await copy_file_or_directory_to_container(file_path, container_save_path)

    output_data = await get_data_from_container_from_code(analysis_result.python_code, analysis_result.output_variable)

    output_data = serialize_raw_data_for_aggregation_object_for_api(output_data)


    payload = AggregationObjectWithRawData(
        **aggregation_object_in_db.model_dump(),
        data=output_data,
    )

    return payload