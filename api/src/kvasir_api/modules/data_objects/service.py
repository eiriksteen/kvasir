import json
import uuid
import numpy as np
import pandas as pd
import jsonschema
from typing import List, Optional, Union, Any, Annotated, Tuple, Dict
from datetime import datetime, timezone
from sqlalchemy import insert, select, update, delete
from fastapi import HTTPException, Depends

from kvasir_api.auth.service import get_current_user
from kvasir_api.auth.schema import User
from kvasir_api.modules.data_objects.models import (
    dataset,
    time_series,
    object_group,
    data_object,
    time_series_group,
    tabular_group,
    tabular,
)
from kvasir_api.modules.visualization.service import Visualizations
from kvasir_api.database.service import execute, fetch_all, insert_df
from kvasir_api.app_secrets import API_URL
from kvasir_ontology.entities.dataset.data_model import (
    DatasetBase,
    DataObjectBase,
    ObjectGroupBase,
    TimeSeriesBase,
    TabularRowBase,
    TimeSeriesGroupBase,
    TabularGroupBase,
    Dataset,
    DataObject,
    ObjectGroup,
    ObjectGroupWithObjects,
    DatasetCreate,
    ObjectGroupCreate,
    DataObjectCreate,
    ObjectsFile,
)
from kvasir_ontology.entities.dataset.interface import DatasetInterface
from kvasir_ontology.visualization.data_model import EchartCreate

# Table mapping for different modalities
GROUP_MODALITY_TABLE_MAPPING = {
    "time_series_group": time_series_group,
    "tabular_group": tabular_group,
}

OBJECT_MODALITY_TABLE_MAPPING = {
    "time_series": time_series,
    "tabular": tabular,
}


def _get_modality_table_and_model(modality: str, entity_type: str):
    """Helper to get table, table name, and model class for a modality"""
    if entity_type == "object_group":
        table = GROUP_MODALITY_TABLE_MAPPING.get(f"{modality}_group")
        table_name = f"{modality}_group"
        if modality == "time_series":
            model_class = TimeSeriesGroupBase
        elif modality == "tabular":
            model_class = TabularGroupBase
        else:
            raise ValueError(f"Unknown modality: {modality}")
    elif entity_type == "data_object":
        table = OBJECT_MODALITY_TABLE_MAPPING.get(modality)
        table_name = modality
        if modality == "time_series":
            model_class = TimeSeriesBase
        elif modality == "tabular":
            model_class = TabularRowBase
        else:
            raise ValueError(f"Unknown modality: {modality}")
    else:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    return table, table_name, model_class


def _convert_numpy_to_native(obj: Any) -> Any:
    """
    Recursively convert all numpy arrays in a data structure to native Python types.
    """
    if isinstance(obj, np.ndarray):
        if obj.size == 1:
            return _convert_numpy_to_native(obj.item())
        else:
            return [_convert_numpy_to_native(item) for item in obj.tolist()]
    elif isinstance(obj, dict):
        return {key: _convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_to_native(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return obj


class Datasets(DatasetInterface):
    def __init__(self, user_id: uuid.UUID, bearer_token: Optional[str] = None):
        super().__init__(user_id, bearer_token)
        self.visualization_service = Visualizations(user_id)

    async def create_dataset(self, dataset_create: DatasetCreate, filename_to_dataframe: Optional[Dict[str, pd.DataFrame]] = None) -> Dataset:
        extra_fields = dataset_create.model_extra or {}

        dataset_obj = DatasetBase(
            id=uuid.uuid4(),
            user_id=self.user_id,
            **dataset_create.model_dump(exclude={'groups'}),
            additional_variables=extra_fields if extra_fields else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(dataset).values(dataset_obj.model_dump()), commit_after=True)

        for group_create in dataset_create.groups:
            group_filename_to_dataframe = {}
            if filename_to_dataframe and group_create.objects_files:
                for objects_file in group_create.objects_files:
                    if objects_file.filename in filename_to_dataframe:
                        group_filename_to_dataframe[objects_file.filename] = filename_to_dataframe[objects_file.filename]

            await self.add_object_group(dataset_obj.id, group_create, group_filename_to_dataframe)

        return await self.get_dataset(dataset_obj.id)

    async def add_object_group(self, dataset_id: uuid.UUID, object_group_create: ObjectGroupCreate, filename_to_dataframe: Dict[str, pd.DataFrame]) -> ObjectGroup:
        if len(filename_to_dataframe) == 0 or not object_group_create.objects_files:
            raise HTTPException(
                status_code=400,
                detail="Object group must have data objects. Provide both filename_to_dataframe and objects_files."
            )

        modality_table, _, modality_model_class = _get_modality_table_and_model(
            object_group_create.modality, "object_group")

        object_group_data = ObjectGroupBase(
            id=uuid.uuid4(),
            **object_group_create.model_dump(exclude={'modality_fields', 'objects_files'}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            additional_variables=object_group_create.model_extra if object_group_create.model_extra else None,
        )

        modality_group_data = modality_model_class(
            id=object_group_data.id,
            **object_group_create.modality_fields.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(object_group).values(object_group_data.model_dump()), commit_after=True)
        await execute(insert(modality_table).values(modality_group_data.model_dump()), commit_after=True)

        # Always create data objects - matching by filename
        await self.add_data_objects(object_group_data.id, object_group_create.objects_files, filename_to_dataframe)

        return await self.get_object_group(object_group_data.id)

    async def add_data_objects(self, object_group_id: uuid.UUID, metadata: List[ObjectsFile], filename_to_dataframe: Dict[str, pd.DataFrame]) -> List[DataObject]:
        created_objects = []

        for objects_file in metadata:
            if objects_file.filename not in filename_to_dataframe:
                raise HTTPException(
                    status_code=400,
                    detail=f"No dataframe found for file: {objects_file.filename}"
                )

            df = filename_to_dataframe[objects_file.filename]
            if len(df) == 0:
                raise HTTPException(
                    status_code=400, detail="DataFrame is empty")

            # Use map() for pandas 2.0+, fallback to applymap() for older versions
            try:
                df = df.map(_convert_numpy_to_native)
            except AttributeError:
                # Fallback for pandas < 2.0
                df = df.applymap(_convert_numpy_to_native)

            first_row = df.iloc[0].to_dict()
            try:
                jsonschema.validate(
                    first_row, DataObjectCreate.model_json_schema())
            except jsonschema.ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Get parent fields from DataObjectBase, excluding auto-generated fields
            parent_fields = set(DataObjectBase.model_fields.keys()) - \
                {"id", "created_at", "updated_at", "group_id"}
            parent_df = df[[
                col for col in parent_fields if col in df.columns]].copy()

            # Extract modality fields from the nested modality_fields column
            if "modality_fields" not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"DataFrame missing required 'modality_fields' column"
                )
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
            now = datetime.now(timezone.utc)

            parent_df["id"] = object_ids
            parent_df["created_at"] = now
            parent_df["updated_at"] = now
            parent_df["group_id"] = object_group_id

            modality_fields_df["id"] = object_ids
            modality_fields_df["created_at"] = now
            modality_fields_df["updated_at"] = now

            _, modality_table_name, _ = _get_modality_table_and_model(
                objects_file.modality, "data_object")

            await insert_df(parent_df, table_name="data_object", schema_name="data_objects")
            await insert_df(modality_fields_df, table_name=modality_table_name, schema_name="data_objects")

            # Get the created objects
            created_objects.extend(await self.get_data_objects(object_ids=object_ids))

        return created_objects

    async def get_datasets(self, dataset_ids: Optional[List[uuid.UUID]] = None) -> List[Dataset]:
        """Get all datasets for a user"""
        datasets_query = select(dataset).where(
            dataset.c.user_id == self.user_id)

        if dataset_ids is not None:
            datasets_query = datasets_query.where(
                dataset.c.id.in_(dataset_ids))

        datasets_result = await fetch_all(datasets_query)

        if not datasets_result:
            return []

        # Get all object groups
        dataset_ids_list = [d["id"] for d in datasets_result]
        object_groups_query = select(object_group).where(
            object_group.c.dataset_id.in_(dataset_ids_list)
        )
        object_groups_result = await fetch_all(object_groups_query)

        group_ids = [group["id"] for group in object_groups_result]

        # Query modality-specific group tables if we have group_ids
        time_series_groups_result = []
        tabular_groups_result = []
        if group_ids:
            time_series_groups_query = select(time_series_group).where(
                time_series_group.c.id.in_(group_ids)
            )
            time_series_groups_result = await fetch_all(time_series_groups_query)

            tabular_groups_query = select(tabular_group).where(
                tabular_group.c.id.in_(group_ids)
            )
            tabular_groups_result = await fetch_all(tabular_groups_query)

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
                first_objects = await self.get_data_objects(object_ids=first_object_ids)
                first_data_objects = {
                    obj.group_id: obj for obj in first_objects}

        # Prepare the final records
        result_records = []
        for dataset_result in datasets_result:
            dataset_obj = DatasetBase(**dataset_result)

            # Create object groups
            all_object_groups: List[ObjectGroup] = []
            for group in object_groups_result:
                if group["dataset_id"] == dataset_obj.id:
                    if group["modality"] == "time_series":
                        modality_record = next(
                            (ts_record for ts_record in time_series_groups_result if ts_record["id"] == group["id"]), None)
                        if modality_record is None:
                            raise ValueError(
                                f"Time series group data not found for group {group['id']}")
                        modality_fields = TimeSeriesGroupBase(
                            **modality_record)
                    elif group["modality"] == "tabular":
                        modality_record = next(
                            (tab_record for tab_record in tabular_groups_result if tab_record["id"] == group["id"]), None)
                        if modality_record is None:
                            raise ValueError(
                                f"Tabular group data not found for group {group['id']}")
                        modality_fields = TabularGroupBase(**modality_record)
                    else:
                        raise ValueError(
                            f"Unknown modality: {group['modality']}")

                    # Create ObjectGroup
                    first_data_object = first_data_objects.get(group["id"])
                    if first_data_object is None:
                        raise ValueError(
                            f"Object group {group['id']} has no data objects. Groups must have at least one data object.")
                    object_group_obj = ObjectGroup(
                        **group,
                        modality_fields=modality_fields,
                        first_data_object=first_data_object
                    )
                    all_object_groups.append(object_group_obj)

            record = Dataset(
                **dataset_obj.model_dump(),
                object_groups=all_object_groups
            )

            result_records.append(record)

        return result_records

    async def get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        datasets = await self.get_datasets([dataset_id])
        if not datasets:
            raise HTTPException(
                status_code=404, detail=f"Dataset with id {dataset_id} not found")
        return datasets[0]

    async def get_object_groups(
        self,
        group_ids: Optional[List[uuid.UUID]] = None,
        dataset_id: Optional[uuid.UUID] = None,
        include_objects: bool = False,
    ) -> List[Union[ObjectGroupWithObjects, ObjectGroup]]:
        object_group_query = select(object_group)

        if dataset_id is not None:
            object_group_query = object_group_query.where(
                object_group.c.dataset_id == dataset_id)
        if group_ids is not None:
            object_group_query = object_group_query.where(
                object_group.c.id.in_(group_ids))

        object_groups_result = await fetch_all(object_group_query)
        object_group_ids = [group["id"] for group in object_groups_result]

        time_series_groups_result = []
        tabular_groups_result = []
        if object_group_ids:
            time_series_groups_query = select(time_series_group).where(
                time_series_group.c.id.in_(object_group_ids))
            time_series_groups_result = await fetch_all(time_series_groups_query)

            tabular_groups_query = select(tabular_group).where(
                tabular_group.c.id.in_(object_group_ids))
            tabular_groups_result = await fetch_all(tabular_groups_query)

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
                first_objects = await self.get_data_objects(object_ids=first_object_ids)
                first_data_objects = {
                    obj.group_id: obj for obj in first_objects}

        data_object_records = None
        if include_objects:
            data_object_records = await self.get_data_objects(group_ids=object_group_ids)

        result_records = []
        for group in object_groups_result:
            if group["modality"] == "time_series":
                structure_fields = next(
                    (ts_group for ts_group in time_series_groups_result if ts_group["id"] == group["id"]), None)
                if structure_fields is None:
                    raise ValueError(
                        f"Time series group data not found for group {group['id']}")
                modality_fields = TimeSeriesGroupBase(**structure_fields)
            elif group["modality"] == "tabular":
                structure_fields = next(
                    (tab_group for tab_group in tabular_groups_result if tab_group["id"] == group["id"]), None)
                if structure_fields is None:
                    raise ValueError(
                        f"Tabular group data not found for group {group['id']}")
                modality_fields = TabularGroupBase(**structure_fields)
            else:
                raise ValueError(f"Unknown modality: {group['modality']}")

            first_data_object = first_data_objects.get(group["id"])
            if first_data_object is None:
                raise ValueError(
                    f"Object group {group['id']} has no data objects. Groups must have at least one data object.")

            if include_objects:
                objects_in_group = [
                    obj_rec for obj_rec in data_object_records if obj_rec.group_id == group["id"]]
                result_records.append(ObjectGroupWithObjects(
                    **ObjectGroupBase(**group).model_dump(),
                    modality_fields=modality_fields,
                    first_data_object=first_data_object,
                    objects=objects_in_group
                ))
            else:
                result_records.append(ObjectGroup(
                    **ObjectGroupBase(**group).model_dump(),
                    modality_fields=modality_fields,
                    first_data_object=first_data_object
                ))

        return result_records

    async def get_object_group(self, group_id: uuid.UUID) -> ObjectGroup:
        groups = await self.get_object_groups(group_ids=[group_id])
        if not groups:
            raise HTTPException(
                status_code=404, detail=f"Object group with id {group_id} not found")
        return groups[0]

    async def get_data_objects(
        self,
        object_ids: Optional[List[uuid.UUID]] = None,
        group_ids: Optional[List[uuid.UUID]] = None
    ) -> List[DataObject]:
        if object_ids is None and group_ids is None:
            raise ValueError("Either object_ids or group_ids must be provided")

        objects_query = select(
            data_object,
            object_group.c.modality
        ).join(
            object_group,
            data_object.c.group_id == object_group.c.id
        )

        if object_ids is not None:
            objects_query = objects_query.where(
                data_object.c.id.in_(object_ids))
        if group_ids is not None:
            objects_query = objects_query.where(
                data_object.c.group_id.in_(group_ids))

        objects_result = await fetch_all(objects_query)

        if not objects_result:
            return []

        object_ids_list = [obj["id"] for obj in objects_result]

        time_series_objects_list = await fetch_all(select(time_series).where(time_series.c.id.in_(object_ids_list)))
        tabular_objects_list = await fetch_all(select(tabular).where(tabular.c.id.in_(object_ids_list)))

        time_series_objects = {ts_obj["id"]: TimeSeriesBase(
            **ts_obj) for ts_obj in time_series_objects_list}
        tabular_objects = {tab_obj["id"]: TabularRowBase(
            **tab_obj) for tab_obj in tabular_objects_list}

        result_records = []
        for obj in objects_result:
            object_id = obj["id"]
            modality = obj["modality"]
            data_object_record = DataObjectBase(**obj)

            if modality == "time_series":
                modality_record = time_series_objects.get(object_id)
                if modality_record is None:
                    raise ValueError(
                        f"Time series object not found for id {object_id}")
            elif modality == "tabular":
                modality_record = tabular_objects.get(object_id)
                if modality_record is None:
                    raise ValueError(
                        f"Tabular object not found for id {object_id}")
            else:
                raise ValueError(f"Unknown modality: {modality}")

            result_records.append(DataObject(
                **data_object_record.model_dump(),
                modality_fields=modality_record,
            ))

        return result_records

    async def get_data_object(self, object_id: uuid.UUID) -> DataObject:
        objects = await self.get_data_objects(object_ids=[object_id])
        if not objects:
            raise HTTPException(
                status_code=404, detail=f"Data object with id {object_id} not found")
        return objects[0]

    async def create_object_group_echart(self, object_group_id: uuid.UUID, echart: EchartCreate) -> ObjectGroup:
        echart_obj = (await self.visualization_service.create_echarts([echart]))[0]

        update_stmt = (
            update(object_group)
            .where(object_group.c.id == object_group_id)
            .values(
                echart_id=echart_obj.id,
                updated_at=datetime.now(timezone.utc)
            )
        )

        await execute(update_stmt, commit_after=True)

        return await self.get_object_group(object_group_id)

    async def delete_dataset(self, dataset_id: uuid.UUID) -> None:
        await self.get_dataset(dataset_id)

        object_groups_query = select(object_group).where(
            object_group.c.dataset_id == dataset_id
        )
        object_groups_result = await fetch_all(object_groups_query)
        object_group_ids = [og["id"] for og in object_groups_result]

        if object_group_ids:
            data_objects_query = select(data_object).where(
                data_object.c.group_id.in_(object_group_ids)
            )
            data_objects_result = await fetch_all(data_objects_query)
            data_object_ids = [do["id"] for do in data_objects_result]

            if data_object_ids:
                await execute(
                    delete(time_series).where(
                        time_series.c.id.in_(data_object_ids)
                    ),
                    commit_after=True
                )

                await execute(
                    delete(tabular).where(
                        tabular.c.id.in_(data_object_ids)
                    ),
                    commit_after=True
                )

                await execute(
                    delete(data_object).where(
                        data_object.c.id.in_(data_object_ids)
                    ),
                    commit_after=True
                )

            await execute(
                delete(time_series_group).where(
                    time_series_group.c.id.in_(object_group_ids)
                ),
                commit_after=True
            )

            await execute(
                delete(tabular_group).where(
                    tabular_group.c.id.in_(object_group_ids)
                ),
                commit_after=True
            )

            await execute(
                delete(object_group).where(
                    object_group.c.id.in_(object_group_ids)
                ),
                commit_after=True
            )

        await execute(
            delete(dataset).where(
                dataset.c.id == dataset_id
            ),
            commit_after=True
        )

    async def get_dataset_submission_code(self) -> Tuple[str, str]:
        """Placeholder for dataset submission code"""
        submission_code = "# TODO: Implement dataset submission code"
        submission_description = "TODO: Implement dataset submission description"
        return submission_code, submission_description

    async def get_object_group_submission_code(self) -> Tuple[str, str]:
        if not self.bearer_token:
            raise ValueError(
                "bearer_token is required for object group submission")

        bearer_token_value = self.bearer_token
        api_url_value = API_URL

        submission_code = (
            f"import requests\n"
            f"import json\n"
            f"import pandas as pd\n"
            f"from io import BytesIO\n"
            f"\n"
            f"# Submit object groups to the API\n"
            f"# The object_groups_dict should be a dictionary or list of dictionaries following the ObjectGroupCreate schema\n"
            f"# It must include 'dataset_id' and the object group fields\n"
            f"# The dataframes_dict should map filenames to pandas DataFrames\n"
            f"\n"
            f"# Check that dataframes_dict exists\n"
            f"if 'dataframes_dict' not in locals() and 'dataframes_dict' not in globals():\n"
            f"    raise ValueError(\"dataframes_dict variable not found. The agent must create a dictionary mapping filenames to DataFrames.\")\n"
            f"\n"
            f"# Handle both single dict and list of dicts\n"
            f"if isinstance(object_groups_dict, dict):\n"
            f"    object_groups_list = [object_groups_dict]\n"
            f"else:\n"
            f"    object_groups_list = object_groups_dict\n"
            f"\n"
            f"results = []\n"
            f"for og_dict in object_groups_list:\n"
            f"    dataset_id = og_dict.get('dataset_id')\n"
            f"    if not dataset_id:\n"
            f"        raise ValueError(\"Each object group dictionary must include 'dataset_id'\")\n"
            f"    \n"
            f"    # Metadata must include dataset_id for ObjectGroupCreate schema validation\n"
            f"    # (even though it's also in the URL path)\n"
            f"    metadata = og_dict.copy()\n"
            f"    \n"
            f"    # Prepare files for upload by converting DataFrames to parquet bytes\n"
            f"    # The 'objects_files' list in metadata maps filenames to their modality\n"
            f"    # Each filename should be a key in dataframes_dict\n"
            f"    files = []\n"
            f"    objects_files = metadata.get('objects_files', [])\n"
            f"    for objects_file in objects_files:\n"
            f"        filename = objects_file.get('filename')\n"
            f"        if not filename:\n"
            f"            raise ValueError(\"Each ObjectsFile must have a 'filename' field\")\n"
            f"        \n"
            f"        # Get the DataFrame from dataframes_dict\n"
            f"        if filename not in dataframes_dict:\n"
            f"            raise KeyError(f\"DataFrame not found for filename '{{filename}}' in dataframes_dict. Available keys: {{list(dataframes_dict.keys())}}\")\n"
            f"        \n"
            f"        df = dataframes_dict[filename]\n"
            f"        if not isinstance(df, pd.DataFrame):\n"
            f"            raise TypeError(f\"Value for filename '{{filename}}' must be a pandas DataFrame, got {{type(df)}}\")\n"
            f"        \n"
            f"        # Convert DataFrame to parquet bytes in memory\n"
            f"        buffer = BytesIO()\n"
            f"        df.to_parquet(buffer, index=False)\n"
            f"        buffer.seek(0)\n"
            f"        parquet_bytes = buffer.read()\n"
            f"        buffer.close()\n"
            f"        \n"
            f"        files.append(('files', (filename, parquet_bytes, 'application/octet-stream')))\n"
            f"    \n"
            f"    if not files:\n"
            f"        raise ValueError(\"No files prepared for upload. The 'objects_files' list must contain valid filenames that exist in dataframes_dict.\")\n"
            f"    \n"
            f"    url = f\"{api_url_value}/data-objects/object-group/{{dataset_id}}\"\n"
            f"    headers = {{\n"
            f"        \"Authorization\": \"Bearer {bearer_token_value}\"\n"
            f"    }}\n"
            f"    \n"
            f"    # Prepare form data with metadata and files\n"
            f"    data = {{\n"
            f"        'metadata': json.dumps(metadata)\n"
            f"    }}\n"
            f"    \n"
            f"    # Submit with multipart/form-data (files + metadata)\n"
            f"    response = requests.post(url, headers=headers, data=data, files=files)\n"
            f"    \n"
            f"    # Check for errors and show detailed error message\n"
            f"    if not response.ok:\n"
            f"        error_detail = response.text\n"
            f"        try:\n"
            f"            error_json = response.json()\n"
            f"            error_detail = json.dumps(error_json, indent=2)\n"
            f"        except:\n"
            f"            pass\n"
            f"        raise requests.exceptions.HTTPError(\n"
            f"            f\"HTTP {{response.status_code}} Error: {{response.reason}}\\n\"\n"
            f"            f\"Response: {{error_detail}}\"\n"
            f"        )\n"
            f"    \n"
            f"    result = response.json()\n"
            f"    results.append(result)\n"
            f"\n"
            f"# Print results as JSON\n"
            f"if len(results) == 1:\n"
            f"    print(json.dumps(results[0], default=str))\n"
            f"else:\n"
            f"    print(json.dumps(results, default=str))\n"
        )

        submission_description = (
            "The submission code expects two variables that you must create:\n"
            "1. 'object_groups_dict': A dictionary or list of dictionaries following the ObjectGroupCreate schema\n"
            "2. 'dataframes_dict': A dictionary mapping filenames to pandas DataFrames\n"
            "\n"
            "IMPORTANT - Keep all data in-memory as DataFrames. DO NOT save to disk.\n"
            "\n"
            "object_groups_dict must include:\n"
            "- 'dataset_id': The UUID of the dataset to add the object group to (must be provided in the prompt)\n"
            "- 'name': Name of the object group\n"
            "- 'modality': The modality type (e.g., 'time_series', 'tabular')\n"
            "- 'modality_fields': Dictionary with modality-specific fields (aggregated statistics for the group)\n"
            "- 'objects_files': List of ObjectsFile dictionaries that map filenames to their metadata\n"
            "  Each ObjectsFile must have:\n"
            "    - 'filename': The filename (must be a key in dataframes_dict)\n"
            "    - 'modality': The modality type for that file\n"
            "- Additional fields as needed for the ObjectGroupCreate schema\n"
            "\n"
            "CRITICAL - DataFrame Structure:\n"
            "Each DataFrame in dataframes_dict must have columns that match the DataObjectCreate schema.\n"
            "Each row represents ONE data object (e.g., one time series, one image, one document) with its metadata.\n"
            "\n"
            "Required columns (from DataObjectCreate schema):\n"
            "- 'name': str - Name of the data object\n"
            "- 'original_id': str - Original identifier for the data object\n"
            "- 'description': Optional[str] - Description of the data object\n"
            "- 'modality_fields': dict - Dictionary containing modality-specific metadata\n"
            "  The structure of modality_fields depends on the modality type and must match the corresponding\n"
            "  Create schema (TimeSeriesCreate for 'time_series', TabularRowCreate for 'tabular', etc.)\n"
            "\n"
            "Example structure:\n"
            "  # Create DataFrame where each row = one data object\n"
            "  objects_df = pd.DataFrame([\n"
            "    {{\n"
            "      'name': 'object_1',\n"
            "      'original_id': 'obj_1',\n"
            "      'description': 'First data object',\n"
            "      'modality_fields': {{...}}  # Structure depends on modality type\n"
            "    }},\n"
            "    {{\n"
            "      'name': 'object_2',\n"
            "      'original_id': 'obj_2',\n"
            "      'description': 'Second data object',\n"
            "      'modality_fields': {{...}}\n"
            "    }}\n"
            "  ])\n"
            "  \n"
            "  dataframes_dict = {{'objects.parquet': objects_df}}\n"
            "  \n"
            "  object_groups_dict = {{\n"
            "    'dataset_id': '...',\n"
            "    'name': 'my_object_group',\n"
            "    'modality': 'time_series',  # or 'tabular', etc.\n"
            "    'modality_fields': {{...}},  # Aggregated stats for all objects in the group\n"
            "    'objects_files': [\n"
            "      {{'filename': 'objects.parquet', 'modality': 'time_series'}}\n"
            "    ]\n"
            "  }}\n"
            "\n"
            "The submission code will:\n"
            "- Convert each DataFrame in dataframes_dict to parquet bytes in memory\n"
            "- Upload the parquet files along with the metadata to the API endpoint\n"
            "- Print the response(s) as JSON\n"
        )

        return submission_code, submission_description

    async def get_data_object_submission_code(self) -> Tuple[str, str]:
        """Placeholder for data object submission code"""
        submission_code = "# TODO: Implement data object submission code"
        submission_description = "TODO: Implement data object submission description"
        return submission_code, submission_description


# For dependency injection
async def get_datasets_service(user: Annotated[User, Depends(get_current_user)]) -> DatasetInterface:
    return Datasets(user.id)
