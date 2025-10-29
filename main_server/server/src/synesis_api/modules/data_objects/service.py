import io
import uuid
import pandas as pd
import jsonschema
from typing import List, Optional, Union, Tuple, Type
from datetime import datetime
from sqlalchemy import insert, select
from fastapi import UploadFile
from pydantic import BaseModel

from synesis_api.modules.data_objects.description import get_dataset_description
from synesis_api.modules.data_sources.service import get_user_data_sources
from synesis_api.modules.pipeline.service import get_user_pipelines
from synesis_api.modules.data_objects.models import (
    dataset,
    time_series,
    object_group,
    data_object,
    time_series_group,
    object_group_from_pipeline,
    object_group_from_data_source,
)
from synesis_schemas.main_server import (
    DatasetCreate,
    DatasetInDB,
    ObjectGroupWithObjects,
    DataObjectInDB,
    TimeSeriesInDB,
    Dataset,
    DataObject,
    ObjectGroupWithObjects,
    DatasetSources,
    ObjectGroup,
    ObjectGroupSources,
    get_data_objects_in_db_info,
    MetadataFile
)
from pandas.io.json._table_schema import build_table_schema
from synesis_api.database.service import execute, fetch_all, insert_df


async def create_dataset_metadata(
    user_id: uuid.UUID,
    dataset_id: uuid.UUID,
    files: List[UploadFile],
    metadata_files: List[MetadataFile]
) -> Dataset:

    for file in files:
        mapping_obj = next(
            m for m in metadata_files if m.filename == file.filename)
        in_db_model_info = get_data_objects_in_db_info(
            mapping_obj.modality, mapping_obj.type)

        content = await file.read()
        df = pd.read_parquet(io.BytesIO(content))
        df_schema = build_table_schema(df)

        jsonschema.validate(
            df_schema, in_db_model_info.create_model.model_json_schema())

        parent_df, child_df = _split_create_df_into_parent_and_child(
            df, in_db_model_info.parent_model, in_db_model_info.child_model)

        parent_df["id"] = uuid.uuid4()
        parent_df["created_at"] = datetime.now()
        parent_df["updated_at"] = datetime.now()
        child_df["id"] = parent_df["id"]
        child_df["created_at"] = parent_df["created_at"]
        child_df["updated_at"] = parent_df["updated_at"]

        if mapping_obj.type == "object":
            parent_df["group_id"] = uuid.uuid4()
        elif mapping_obj.type == "object_group":
            parent_df["dataset_id"] = dataset_id

        await insert_df(parent_df, table_name=in_db_model_info.parent_table_name)
        await insert_df(child_df, table_name=in_db_model_info.child_table_name)

    # Return the created dataset
    return await get_user_datasets(user_id, dataset_ids=[dataset_id])[0]


async def create_dataset(
        user_id: uuid.UUID,
        files: List[UploadFile],
        dataset_create: DatasetCreate) -> Dataset:

    dataset_obj = DatasetInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=dataset_create.name,
        description=dataset_create.description,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    await execute(insert(dataset).values(dataset_obj.model_dump()), commit_after=True)

    return await create_dataset_metadata(user_id, dataset_obj.id, files, dataset_create.metadata_files)


async def get_user_datasets(
        user_id: uuid.UUID,
        dataset_ids: Optional[List[uuid.UUID]] = None
) -> List[Dataset]:
    """Get all datasets for a user"""

    # Get all datasets for the user
    datasets_query = select(dataset).where(dataset.c.user_id == user_id)

    if dataset_ids is not None:
        datasets_query = datasets_query.where(dataset.c.id.in_(dataset_ids))

    datasets_result = await fetch_all(datasets_query)

    if not datasets_result:
        return []

    # Get all object groups
    dataset_ids = [d["id"] for d in datasets_result]
    object_groups_query = select(object_group).where(
        object_group.c.dataset_id.in_(dataset_ids)
    )
    object_groups_result = await fetch_all(object_groups_query)

    group_ids = [group["id"] for group in object_groups_result]

    # Get pipeline IDs from object groups
    pipeline_ids_query = select(object_group_from_pipeline).where(
        object_group_from_pipeline.c.object_group_id.in_(group_ids)
    )
    pipeline_ids_result = await fetch_all(pipeline_ids_query)

    # Get data source IDs from object groups
    data_source_ids_query = select(object_group_from_data_source).where(
        object_group_from_data_source.c.object_group_id.in_(group_ids)
    )
    data_source_ids_result = await fetch_all(data_source_ids_query)

    time_series_groups_query = select(time_series_group).where(
        time_series_group.c.id.in_(group_ids)
    )
    time_series_groups_result = await fetch_all(time_series_groups_query)

    # Get all unique pipeline and data source IDs to fetch full objects
    all_pipeline_ids = list(set([rec["pipeline_id"]
                            for rec in pipeline_ids_result]))
    all_data_source_ids = list(
        set([rec["data_source_id"] for rec in data_source_ids_result]))

    # Fetch full pipeline and data source objects
    pipelines = await get_user_pipelines(user_id, all_pipeline_ids)
    data_sources = await get_user_data_sources(user_id, all_data_source_ids)

    # Create lookup dictionaries for quick access
    pipeline_lookup = {p.id: p for p in pipelines}
    data_source_lookup = {ds.id: ds for ds in data_sources}

    # Prepare the final records
    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)

        # Create object groups with populated sources
        time_series_object_groups: List[ObjectGroup] = []
        for group in object_groups_result:
            if group["dataset_id"] == dataset_obj.id:
                # Get sources for this object group
                group_pipeline_ids = [
                    rec["pipeline_id"] for rec in pipeline_ids_result if rec["object_group_id"] == group["id"]]
                group_data_source_ids = [
                    rec["data_source_id"] for rec in data_source_ids_result if rec["object_group_id"] == group["id"]]

                # Get full objects
                group_pipelines = [pipeline_lookup[pid]
                                   for pid in group_pipeline_ids if pid in pipeline_lookup]
                group_data_sources = [data_source_lookup[dsid]
                                      for dsid in group_data_source_ids if dsid in data_source_lookup]

                # Create ObjectGroupSources
                object_group_sources = ObjectGroupSources(
                    data_sources=group_data_sources,
                    pipelines=group_pipelines
                )

                if group["modality"] == "time_series":
                    ts_record = next(
                        (ts_record for ts_record in time_series_groups_result if ts_record["id"] == group["id"]), None)
                else:
                    raise ValueError(
                        f"Unknown modality: {group['modality']}")

                # Create ObjectGroup with sources
                object_group_obj = ObjectGroup(
                    **group,
                    modality_fields=ts_record,
                    sources=object_group_sources
                )
                time_series_object_groups.append(object_group_obj)

        all_object_groups = time_series_object_groups
        # TODO: Add other object groups here

        # Compute dataset sources from populated object groups
        dataset_pipeline_ids = []
        dataset_data_source_ids = []
        for obj_group in all_object_groups:
            dataset_pipeline_ids.extend(
                [p.id for p in obj_group.sources.pipelines])
            dataset_data_source_ids.extend(
                [ds.id for ds in obj_group.sources.data_sources])

        sources = DatasetSources(
            pipeline_ids=list(set(dataset_pipeline_ids)),
            data_source_ids=list(set(dataset_data_source_ids))
        )

        description = get_dataset_description(
            dataset_obj,
            all_object_groups,
            include_full_data_source_description=True,
            include_full_pipeline_description=True
        )

        record = Dataset(
            **dataset_obj.model_dump(),
            object_groups=all_object_groups,
            sources=sources,
            description_for_agent=description
        )

        result_records.append(record)

    return result_records


async def get_object_groups(
    user_id: uuid.UUID,
    dataset_id: Optional[uuid.UUID] = None,
    group_ids: Optional[List[uuid.UUID]] = None,
    include_objects: bool = False,
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

    time_series_groups_query = select(time_series_group).where(
        time_series_group.c.id.in_(object_group_ids))
    time_series_groups_result = await fetch_all(time_series_groups_query)

    # Get pipeline and data source IDs for these object groups
    pipeline_ids_query = select(object_group_from_pipeline).where(
        object_group_from_pipeline.c.object_group_id.in_(object_group_ids)
    )
    pipeline_ids_result = await fetch_all(pipeline_ids_query)

    data_source_ids_query = select(object_group_from_data_source).where(
        object_group_from_data_source.c.object_group_id.in_(object_group_ids)
    )
    data_source_ids_result = await fetch_all(data_source_ids_query)

    # Get all unique pipeline and data source IDs to fetch full objects
    all_pipeline_ids = list(set([rec["pipeline_id"]
                            for rec in pipeline_ids_result]))
    all_data_source_ids = list(
        set([rec["data_source_id"] for rec in data_source_ids_result]))

    pipelines = await get_user_pipelines(user_id, all_pipeline_ids)
    data_sources = await get_user_data_sources(user_id, all_data_source_ids)

    # Create lookup dictionaries for quick access
    pipeline_lookup = {p.id: p for p in pipelines}
    data_source_lookup = {ds.id: ds for ds in data_sources}

    data_object_records = None
    if include_objects:
        data_object_records = await get_data_objects(group_ids=object_group_ids)

    result_records = []
    for group in object_groups_result:
        if group["modality"] == "time_series":
            structure_fields = next(
                (ts_group for ts_group in time_series_groups_result if ts_group["id"] == group["id"]), None)
        else:
            raise ValueError(f"Unknown modality: {group['modality']}")

        # Get sources for this object group
        group_pipeline_ids = [rec["pipeline_id"]
                              for rec in pipeline_ids_result if rec["object_group_id"] == group["id"]]
        group_data_source_ids = [rec["data_source_id"]
                                 for rec in data_source_ids_result if rec["object_group_id"] == group["id"]]

        # Get full objects
        group_pipelines = [pipeline_lookup[pid]
                           for pid in group_pipeline_ids if pid in pipeline_lookup]
        group_data_sources = [data_source_lookup[dsid]
                              for dsid in group_data_source_ids if dsid in data_source_lookup]

        # Create ObjectGroupSources
        object_group_sources = ObjectGroupSources(
            data_sources=group_data_sources,
            pipelines=group_pipelines
        )

        if include_objects:
            objects_in_group = [
                obj_rec for obj_rec in data_object_records if obj_rec.group_id == group["id"]]
            result_records.append(ObjectGroupWithObjects(
                **group,
                modality_fields=structure_fields,
                sources=object_group_sources,
                objects=objects_in_group
            ))
        else:
            result_records.append(ObjectGroup(
                **group,
                modality_fields=structure_fields,
                sources=object_group_sources
            ))

    return result_records


async def get_data_objects(
    object_ids: Optional[List[uuid.UUID]] = None,
    group_ids: Optional[List[uuid.UUID]] = None
) -> List[DataObject]:

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

    result_records = []
    for object_id in object_ids:
        data_object_record = next(DataObjectInDB(**obj)
                                  for obj in objects_result if obj["id"] == object_id)

        time_series_object_record = next((TimeSeriesInDB(
            **obj) for obj in time_series_objects if obj["id"] == object_id), None)

        assert time_series_object_record is not None, "Time series object not found"

        result_records.append(DataObject(
            **data_object_record.model_dump(),
            modality_fields=time_series_object_record,
        ))

    return result_records


##


def _split_create_df_into_parent_and_child(df: pd.DataFrame, parent_model: Type[BaseModel], child_model: Type[BaseModel]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Get fields unique to parent and child
    parent_cols = list(parent_model.model_fields.keys())
    child_cols = list(child_model.model_fields.keys())

    # Remove id and created_at and updated_at since we haven't created them yet
    parent_cols = [c for c in parent_cols if c in df.columns]
    child_cols = [c for c in child_cols if c in df.columns]

    parent_df = df[parent_cols]
    child_df = df[child_cols]

    return parent_df, child_df
