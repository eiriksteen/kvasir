import io
import json
import uuid
import numpy as np
import pandas as pd
import jsonschema
from typing import List, Optional, Union, Any
from datetime import datetime
from sqlalchemy import insert, select, update
from fastapi import UploadFile, HTTPException

from synesis_api.modules.data_objects.models import (
    dataset,
    time_series,
    object_group,
    data_object,
    time_series_group,
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
    ObjectGroup,
    get_modality_models,
    ObjectsFile,
    DataObjectGroupCreate,
    ObjectGroupInDB,
    DataObjectCreate,
    UpdateObjectGroupChartScriptRequest
)
from synesis_api.database.service import execute, fetch_all, insert_df

# Table mapping for different modalities
GROUP_MODALITY_TABLE_MAPPING = {
    "time_series_group": time_series_group,
    # Add new modality tables here as they're created
}


# =============================================================================
# CREATE FUNCTIONS
# =============================================================================


async def create_data_objects(
    group_id: uuid.UUID,
    files: List[UploadFile],
    objects_files: List[ObjectsFile]
) -> List[DataObject]:
    created_objects = []

    for file in files:
        objects_file = next(
            (of for of in objects_files if of.filename == file.filename), None)

        if objects_file is None:
            raise HTTPException(
                status_code=400,
                detail=f"No object file metadata found for filename: {file.filename}"
            )

        modality_models = get_modality_models(
            objects_file.modality, "data_object")

        content = await file.read()
        df = pd.read_parquet(io.BytesIO(content))

        # Validate first row since all rows have the same schema
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="DataFrame is empty")

        # Convert numpy arrays to native Python types for all rows
        df = df.applymap(_convert_numpy_to_native)

        first_row = df.iloc[0].to_dict()
        print("&"*100)
        print("TRYING TO VALIDATE FIRST ROW")
        print(first_row)
        try:
            jsonschema.validate(
                first_row, DataObjectCreate.model_json_schema())
        except jsonschema.ValidationError as e:
            print("&"*100)
            print("VALIDATION ERROR")
            print(e)
            print("&"*100)
            raise HTTPException(status_code=400, detail=str(e))

        # Get parent fields from DataObjectInDB, excluding auto-generated fields
        parent_fields = set(DataObjectInDB.model_fields.keys()) - \
            {"id", "created_at", "updated_at", "group_id"}
        parent_df = df[[
            col for col in parent_fields if col in df.columns]].copy()

        # Extract modality fields from the nested modality_fields column
        # Don't use json_normalize as it will flatten JSONB fields like features_schema
        modality_fields_list = df["modality_fields"].tolist()
        modality_fields_df = pd.DataFrame(modality_fields_list)

        # Convert dict values to JSON strings for JSONB columns
        try:
            for col in modality_fields_df.columns:
                modality_fields_df[col] = modality_fields_df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        object_ids = [uuid.uuid4() for _ in range(len(parent_df))]
        now = datetime.now()

        parent_df["id"] = object_ids
        parent_df["created_at"] = now
        parent_df["updated_at"] = now
        parent_df["group_id"] = group_id

        modality_fields_df["id"] = object_ids
        modality_fields_df["created_at"] = now
        modality_fields_df["updated_at"] = now

        await insert_df(parent_df, table_name="data_object", schema_name="data_objects")
        await insert_df(modality_fields_df, table_name=modality_models.child_table_name, schema_name="data_objects")

        # Get the created objects
        created_objects.extend(await get_data_objects(object_ids=object_ids))

    return created_objects


async def create_object_group(
    dataset_id: uuid.UUID,
    group_create: DataObjectGroupCreate,
    files: List[UploadFile] = []
) -> ObjectGroup:

    modality_models = get_modality_models(
        group_create.modality, "object_group")

    object_group_data = ObjectGroupInDB(
        id=uuid.uuid4(),
        **group_create.model_dump(),
        dataset_id=dataset_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        additional_variables=group_create.__pydantic_extra__,
    )

    # Extract modality-specific fields
    modality_group_data = modality_models.child_model(
        id=object_group_data.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        **group_create.modality_fields.model_dump()
    )
    await execute(insert(object_group).values(object_group_data.model_dump()), commit_after=True)
    modality_table = GROUP_MODALITY_TABLE_MAPPING[modality_models.child_table_name]
    await execute(insert(modality_table).values(modality_group_data.model_dump()), commit_after=True)
    await create_data_objects(object_group_data.id, files, group_create.objects_files)

    object_groups = await get_object_groups(group_ids=[object_group_data.id])
    if not object_groups:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve created object group")
    return object_groups[0]


async def create_dataset(
        user_id: uuid.UUID,
        dataset_create: DatasetCreate,
        files: List[UploadFile] = []) -> Dataset:

    extra_fields = dataset_create.__pydantic_extra__ or {}

    dataset_obj = DatasetInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **dataset_create.model_dump(exclude=list(extra_fields.keys())),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        additional_variables=extra_fields
    )
    await execute(insert(dataset).values(dataset_obj.model_dump()), commit_after=True)

    # Dataset source relationships are now managed by project_graph module

    for group_create in dataset_create.groups:
        # Match files for this group
        group_files = []
        if files and group_create.objects_files:
            for file in files:
                if any(of.filename == file.filename for of in group_create.objects_files):
                    group_files.append(file)

        await create_object_group(dataset_obj.id, group_create, group_files)

    return (await get_user_datasets(user_id, dataset_ids=[dataset_obj.id]))[0]


# =============================================================================
# GET/READ FUNCTIONS
# =============================================================================

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

    # Dataset sources relationships are now managed by project_graph module

    # Only query time series groups if we have group_ids
    time_series_groups_result = []
    if group_ids:
        time_series_groups_query = select(time_series_group).where(
            time_series_group.c.id.in_(group_ids)
        )
        time_series_groups_result = await fetch_all(time_series_groups_query)

    # Get first data object for each group
    first_data_objects = {}
    if group_ids:
        first_object_ids_query = select(
            data_object.c.group_id,
            data_object.c.id
        ).where(
            data_object.c.group_id.in_(group_ids)
        ).order_by(
            data_object.c.group_id,
            data_object.c.created_at
        ).distinct(data_object.c.group_id)

        first_object_ids_result = await fetch_all(first_object_ids_query)
        first_object_ids = [row["id"] for row in first_object_ids_result]

        if first_object_ids:
            first_objects = await get_data_objects(object_ids=first_object_ids)
            first_data_objects = {obj.group_id: obj for obj in first_objects}

    # Prepare the final records
    result_records = []
    for dataset_result in datasets_result:
        dataset_obj = DatasetInDB(**dataset_result)

        # Create object groups
        all_object_groups: List[ObjectGroup] = []
        for group in object_groups_result:
            if group["dataset_id"] == dataset_obj.id:
                if group["modality"] == "time_series":
                    ts_record = next(
                        (ts_record for ts_record in time_series_groups_result if ts_record["id"] == group["id"]), None)
                    if ts_record is None:
                        raise ValueError(
                            f"Time series group data not found for group {group['id']}")
                else:
                    raise ValueError(f"Unknown modality: {group['modality']}")

                # Create ObjectGroup without sources
                object_group_obj = ObjectGroup(
                    **group,
                    modality_fields=ts_record,
                    first_data_object=first_data_objects.get(group["id"])
                )
                all_object_groups.append(object_group_obj)

        # TODO: Add other object groups here

        record = Dataset(
            **dataset_obj.model_dump(),
            object_groups=all_object_groups
        )

        result_records.append(record)

    return result_records


async def get_object_groups(
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

    # Only query time series groups if we have object_group_ids
    time_series_groups_result = []
    if object_group_ids:
        time_series_groups_query = select(time_series_group).where(
            time_series_group.c.id.in_(object_group_ids))
        time_series_groups_result = await fetch_all(time_series_groups_query)

    # Get first data object for each group
    first_data_objects = {}
    if object_group_ids:
        first_object_ids_query = select(
            data_object.c.group_id,
            data_object.c.id
        ).where(
            data_object.c.group_id.in_(object_group_ids)
        ).order_by(
            data_object.c.group_id,
            data_object.c.created_at
        ).distinct(data_object.c.group_id)

        first_object_ids_result = await fetch_all(first_object_ids_query)
        first_object_ids = [row["id"] for row in first_object_ids_result]

        if first_object_ids:
            first_objects = await get_data_objects(object_ids=first_object_ids)
            first_data_objects = {obj.group_id: obj for obj in first_objects}

    data_object_records = None
    if include_objects:
        data_object_records = await get_data_objects(group_ids=object_group_ids)

    result_records = []
    for group in object_groups_result:
        if group["modality"] == "time_series":
            structure_fields = next(
                (ts_group for ts_group in time_series_groups_result if ts_group["id"] == group["id"]), None)
            if structure_fields is None:
                raise ValueError(
                    f"Time series group data not found for group {group['id']}")
        else:
            raise ValueError(f"Unknown modality: {group['modality']}")

        if include_objects:
            objects_in_group = [
                obj_rec for obj_rec in data_object_records if obj_rec.group_id == group["id"]]
            result_records.append(ObjectGroupWithObjects(
                **group,
                modality_fields=structure_fields,
                first_data_object=first_data_objects.get(group["id"]),
                objects=objects_in_group
            ))
        else:
            result_records.append(ObjectGroup(
                **group,
                modality_fields=structure_fields,
                first_data_object=first_data_objects.get(group["id"])
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

    if not objects_result:
        return []

    object_ids = [obj["id"] for obj in objects_result]

    time_series_objects = await fetch_all(select(time_series).where(time_series.c.id.in_(object_ids)))

    result_records = []
    for object_id in object_ids:
        data_object_record = next(
            (DataObjectInDB(**obj) for obj in objects_result if obj["id"] == object_id), None)

        if data_object_record is None:
            raise ValueError(f"Data object not found for id {object_id}")

        time_series_object_record = next(
            (TimeSeriesInDB(**obj) for obj in time_series_objects if obj["id"] == object_id), None)

        if time_series_object_record is None:
            raise ValueError(
                f"Time series object not found for id {object_id}")

        result_records.append(DataObject(
            **data_object_record.model_dump(),
            modality_fields=time_series_object_record,
        ))

    return result_records


# =============================================================================
# UPDATE FUNCTIONS
# =============================================================================

async def update_object_group_chart_script(
    group_id: uuid.UUID,
    request: UpdateObjectGroupChartScriptRequest
) -> ObjectGroup:
    """Update the chart generation script and function name for an object group"""

    # Update the object group
    update_stmt = (
        update(object_group)
        .where(object_group.c.id == group_id)
        .values(
            chart_script_path=request.chart_script_path,
            updated_at=datetime.now()
        )
    )

    await execute(update_stmt, commit_after=True)

    # Return the updated object group
    updated_groups = await get_object_groups(group_ids=[group_id])
    if not updated_groups:
        raise HTTPException(
            status_code=404, detail=f"Object group {group_id} not found")

    return updated_groups[0]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _convert_numpy_to_native(obj: Any) -> Any:
    """
    Recursively convert all numpy arrays in a data structure to native Python types.

    - numpy arrays with a single element are converted to single values
    - numpy arrays with multiple elements are converted to lists
    - Recursively processes dicts and lists
    """
    if isinstance(obj, np.ndarray):
        if obj.size == 1:
            # Single value - extract it
            return _convert_numpy_to_native(obj.item())
        else:
            # Multiple values - convert to list
            return [_convert_numpy_to_native(item) for item in obj.tolist()]
    elif isinstance(obj, dict):
        return {key: _convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_to_native(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        # Convert numpy scalar types to Python native types
        return obj.item()
    else:
        return obj
