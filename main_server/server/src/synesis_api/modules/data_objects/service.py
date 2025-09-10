import uuid
import pandas as pd
from typing import List, Optional, Union
from datetime import datetime, timezone
from sqlalchemy import insert, select, and_
from fastapi import UploadFile

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
    DatasetWithObjectGroups,
    DatasetWithObjectGroupsAndFeatures,
    TimeSeriesFull,
    TimeSeriesAggregationFull,
    ObjectGroupWithEntitiesAndFeatures,
    ObjectGroupsWithEntitiesAndFeaturesInDataset,
)
from synesis_api.database.service import execute, fetch_one, fetch_all

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
        user_id: uuid.UUID) -> DatasetWithObjectGroups:
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

    # Variables to collect object groups for the response
    primary_object_group = None
    annotated_object_groups = []
    computed_object_groups = []

    for (groups, role) in zip(
        ([dataset_create.primary_object_group],
         dataset_create.annotated_object_groups,
         dataset_create.computed_object_groups),
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

            # Collect the object group for the response
            if role == "primary":
                primary_object_group = object_group_record
            elif role == "annotated":
                annotated_object_groups.append(object_group_record)
            elif role == "derived":
                computed_object_groups.append(object_group_record)

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
            is_time_series_structure = dataset_create.primary_object_group.structure_type == TIME_SERIES_STRUCTURE.first_level_id
            is_time_series_aggregation_structure = dataset_create.primary_object_group.structure_type == TIME_SERIES_AGGREGATION_STRUCTURE.first_level_id

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
                        group_id=object_group_record.id,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        additional_variables=additional_metadata.loc[entity_id].to_dict(
                        )
                    )

                    object_records.append(object_record)

                    time_series_record = TimeSeriesInDB(
                        id=object_record.id,
                        **fixed_metadata.loc[entity_id].to_dict()
                    )

                    original_entity_id_to_generated_id[entity_id] = time_series_record.id

                    time_series_records.append(time_series_record)

                await execute(insert(data_object).values(object_records), commit_after=True)
                await execute(insert(time_series).values(time_series_records), commit_after=True)

            elif is_time_series_aggregation_structure:

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
                        group_id=object_group_record.id,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        additional_variables=additional_metadata.loc[aggregation_id].to_dict(
                        )
                    )

                    object_records.append(object_record)

                    time_series_aggregation_record = TimeSeriesAggregationInDB(
                        id=object_record.id,
                        **fixed_metadata.loc[aggregation_id].to_dict()
                    )

                    agg_records.append(time_series_aggregation_record)

                    for agg_input in inputs_metadata.iterrows():
                        time_series_aggregation_input_record = TimeSeriesAggregationInputInDB(
                            id=uuid.uuid4(),
                            time_series_id=original_entity_id_to_generated_id[agg_input["time_series_id"]],
                            aggregation_id=object_record.id,
                            **agg_input.to_dict()
                        )
                        input_records.append(
                            time_series_aggregation_input_record)

                await execute(insert(data_object).values(object_records), commit_after=True)
                await execute(insert(time_series_aggregation).values(agg_records), commit_after=True)
                await execute(insert(time_series_aggregation_input).values(input_records), commit_after=True)

            else:
                raise ValueError(
                    f"Data structure not supported: {structure}")

        # Return the dataset with object groups
        return DatasetWithObjectGroups(
            **dataset_record.model_dump(),
            primary_object_group=primary_object_group,
            annotated_object_groups=annotated_object_groups,
            computed_object_groups=computed_object_groups
        )


async def get_user_datasets(
        user_id: uuid.UUID,
        include_features: bool = False,
) -> List[Union[DatasetWithObjectGroupsAndFeatures, DatasetWithObjectGroups]]:
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
    if include_features:
        object_groups = await _add_features_to_object_groups(object_groups)

    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)
        if len([
                group for group in object_groups if group.dataset_id == dataset_obj.id and group.role == "primary"]) == 0:
            print(
                f"No primary object group found for dataset {dataset_obj.id}")
        primary_object_group = [
            group for group in object_groups if group.dataset_id == dataset_obj.id and group.role == "primary"][0]
        annotated_object_groups = [
            group for group in object_groups if group.dataset_id == dataset_obj.id and group.role == "annotated"]
        computed_object_groups = [
            group for group in object_groups if group.dataset_id == dataset_obj.id and group.role == "derived"]

        if include_features:
            record = DatasetWithObjectGroupsAndFeatures(
                **dataset_obj.model_dump(),
                primary_object_group=primary_object_group,
                annotated_object_groups=annotated_object_groups,
                computed_object_groups=computed_object_groups
            )
        else:
            record = DatasetWithObjectGroups(
                **dataset_obj.model_dump(),
                primary_object_group=primary_object_group,
                annotated_object_groups=annotated_object_groups,
                computed_object_groups=computed_object_groups
            )

        result_records.append(record)

    return result_records


async def get_user_datasets_by_ids(
        user_id: uuid.UUID,
        dataset_ids: List[uuid.UUID] = [],
        max_features: Optional[int] = None,
        include_features: bool = False
) -> List[Union[DatasetWithObjectGroupsAndFeatures, DatasetWithObjectGroups]]:
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
            if include_features:
                primary = (await _add_features_to_object_groups([primary_object_group], max_features))[0]
                annotated = await _add_features_to_object_groups(annotated_object_groups, max_features)
                computed = await _add_features_to_object_groups(computed_object_groups, max_features)

                record = DatasetWithObjectGroupsAndFeatures(
                    **dataset_obj.model_dump(),
                    primary_object_group=primary,
                    annotated_object_groups=annotated,
                    computed_object_groups=computed,
                )
            else:
                record = DatasetWithObjectGroups(
                    **dataset_obj.model_dump(),
                    primary_object_group=primary_object_group,
                    annotated_object_groups=annotated_object_groups,
                    computed_object_groups=computed_object_groups,
                )

            result_datasets.append(record)

    return result_datasets


async def get_user_dataset_by_id(
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        include_features: bool = False
) -> Union[DatasetWithObjectGroupsAndFeatures, DatasetWithObjectGroups]:
    """Get a dataset for a user"""

    return (await get_user_datasets_by_ids(user_id, [dataset_id], include_features=include_features))[0]


async def get_object_groups_in_dataset_with_entities_and_features(dataset_id: uuid.UUID) -> ObjectGroupsWithEntitiesAndFeaturesInDataset:
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

    return ObjectGroupsWithEntitiesAndFeaturesInDataset(
        dataset_id=dataset_id,
        primary_object_group=primary_object_group,
        annotated_object_groups=annotated_object_groups,
        computed_object_groups=computed_object_groups
    )


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
