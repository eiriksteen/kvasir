import io
import uuid
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Annotated, Tuple
from sqlalchemy import insert, select, update, delete
from fastapi import HTTPException, Depends, UploadFile

from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User
from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.entity_graph.service import EntityGraphs
from synesis_api.modules.data_sources.models import (
    file_data_source,
    data_source,
)
from synesis_api.app_secrets import API_URL
from kvasir_ontology.entities.data_source.data_model import (
    DataSourceBase,
    FileDataSourceBase,
    DataSource,
    DataSourceCreate,
    DataSourceDetailsCreate,
    UnknownFileCreate,
)
from kvasir_ontology.entities.data_source.interface import DataSourceInterface
from kvasir_research.sandbox.modal import ModalSandbox


class DataSources(DataSourceInterface):

    async def create_data_source(self, data_source_create: DataSourceCreate) -> DataSource:
        # Get the fields defined in DataSourceCreate (excluding type_fields)
        extra_fields = data_source_create.model_extra or {}

        # Handle additional variables - only if type_fields is provided
        additional_variables = {**extra_fields}
        if data_source_create.type_fields:
            extra_type_fields = data_source_create.type_fields.model_extra or {}
            # We also add all fields present in type fields and not present in unknown file create into the additional variables
            file_type_fields = {k: v for k, v in data_source_create.type_fields.model_dump().items()
                                if k not in UnknownFileCreate.model_fields}
            additional_variables = {**extra_fields,
                                    **extra_type_fields,
                                    **file_type_fields}

        # Create the base data source
        data_source_id = uuid.uuid4()
        data_source_obj = DataSourceBase(
            id=data_source_id,
            user_id=self.user_id,
            **data_source_create.model_dump(exclude={'type_fields'}),
            additional_variables=additional_variables if additional_variables else None,
            created_at=datetime.now(timezone.utc)
        )

        await execute(
            insert(data_source).values(data_source_obj.model_dump()),
            commit_after=True
        )

        # Handle type-specific fields
        type_fields = data_source_create.type_fields
        type_fields_obj = None
        if type_fields:
            if data_source_create.type == "file":
                # Insert into file_data_source table
                file_data_source_obj = FileDataSourceBase(
                    id=data_source_id,
                    **type_fields.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await execute(
                    insert(file_data_source).values(
                        file_data_source_obj.model_dump()),
                    commit_after=True
                )
                type_fields_obj = file_data_source_obj

        return DataSource(
            **data_source_obj.model_dump(),
            type_fields=type_fields_obj
        )

    async def add_data_source_details(self, data_source_id: uuid.UUID, data_source_details: DataSourceDetailsCreate) -> DataSource:
        # First verify the data source exists and belongs to the user
        existing = await self.get_data_sources([data_source_id])
        if not existing:
            raise HTTPException(
                status_code=404, detail="Data source not found")

        data_source_obj = existing[0]

        # Check if details already exist
        if data_source_obj.type_fields is not None:
            raise HTTPException(
                status_code=400, detail="Data source details already exist")

        # Extract additional variables from type_fields
        extra_type_fields = data_source_details.type_fields.model_extra or {}
        file_type_fields = {k: v for k, v in data_source_details.type_fields.model_dump().items()
                            if k not in UnknownFileCreate.model_fields}

        new_additional_variables = {
            **(data_source_obj.additional_variables or {}),
            **extra_type_fields,
            **file_type_fields
        }

        # Update the base data source with additional variables
        await execute(
            update(data_source)
            .where(data_source.c.id == data_source_id)
            .values(additional_variables=new_additional_variables),
            commit_after=True
        )

        # Insert type-specific fields
        type_fields_obj = None
        if data_source_obj.type == "file":
            file_data_source_obj = FileDataSourceBase(
                id=data_source_id,
                **data_source_details.type_fields.model_dump(),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await execute(
                insert(file_data_source).values(
                    file_data_source_obj.model_dump()),
                commit_after=True
            )
            type_fields_obj = file_data_source_obj

        return DataSource(
            **data_source_obj.model_dump(exclude={'additional_variables', 'type_fields'}),
            additional_variables=new_additional_variables,
            type_fields=type_fields_obj
        )

    async def get_data_sources(self, data_source_ids: Optional[List[uuid.UUID]] = None) -> List[DataSource]:
        # Get the base data source
        data_source_query = select(data_source).where(
            data_source.c.user_id == self.user_id
        )
        if data_source_ids is not None:
            data_source_query = data_source_query.where(
                data_source.c.id.in_(data_source_ids)
            )

        source_records = await fetch_all(data_source_query)

        if not source_records:
            return []

        source_ids = [record["id"] for record in source_records]

        # Get file data source records
        file_source_query = select(file_data_source).where(
            file_data_source.c.id.in_(source_ids)
        )
        file_source_records = await fetch_all(file_source_query)

        output_records = []
        for source_id in source_ids:
            source_obj = DataSourceBase(**next(
                iter([record for record in source_records if record["id"] == source_id])))

            file_record = next(
                iter([record for record in file_source_records if record["id"] == source_id]), None)

            type_fields_obj = None
            if file_record:
                type_fields_obj = FileDataSourceBase(**file_record)

            output_records.append(DataSource(
                **source_obj.model_dump(),
                type_fields=type_fields_obj
            ))

        return output_records

    async def get_data_source(self, data_source_id: uuid.UUID) -> DataSource:
        data_sources = await self.get_data_sources([data_source_id])
        if not data_sources:
            raise HTTPException(
                status_code=404, detail=f"Data source with id {data_source_id} not found")
        return data_sources[0]

    async def delete_data_source(self, data_source_id: uuid.UUID) -> None:
        existing = await self.get_data_sources([data_source_id])
        if not existing:
            raise HTTPException(
                status_code=404, detail="Data source not found")

        await execute(delete(file_data_source).where(file_data_source.c.id == data_source_id), commit_after=True)
        await execute(delete(data_source).where(data_source.c.id == data_source_id), commit_after=True)

    async def create_files_data_sources(self, file_bytes: List[io.BytesIO], file_names: List[str], mount_group_id: uuid.UUID) -> Tuple[List[DataSource], List[Path]]:
        """
        Create data sources from uploaded files.
        
        Supports individual files and .zip archives. ZIP files are automatically detected and extracted,
        with each file inside the archive being added as a separate data source.
        
        Args:
            file_bytes: List of file contents as BytesIO objects
            file_names: List of corresponding file names
            mount_group_id: UUID of the mount group to add the data sources to
            
        Returns:
            Tuple of (list of created DataSource objects, list of file paths in the sandbox)
        """
        graph_service = EntityGraphs(self.user_id)
        mount_group = await graph_service.get_node_group(mount_group_id)
        sandbox = ModalSandbox(mount_group_id, mount_group.python_package_name)

        # Process files and extract zip files if present
        processed_files = []
        for file_byte, file_name in zip(file_bytes, file_names):
            # Check if the file is a zip file
            if file_name.lower().endswith('.zip'):
                # Reset the file pointer to the beginning
                file_byte.seek(0)
                try:
                    with zipfile.ZipFile(file_byte, 'r') as zip_ref:
                        # Extract all files from the zip
                        for zip_info in zip_ref.infolist():
                            # Skip directories
                            if zip_info.is_dir():
                                continue
                            
                            # Skip macOS metadata files and hidden files
                            # Common patterns: __MACOSX/, .DS_Store, ._filename (resource forks)
                            if ('__MACOSX' in zip_info.filename or 
                                zip_info.filename.startswith('._') or
                                '/.DS_Store' in zip_info.filename or
                                zip_info.filename == '.DS_Store'):
                                continue
                            
                            # Use only the filename (not the full path in the zip)
                            extracted_name = Path(zip_info.filename).name
                            
                            # Skip if filename is empty (edge case)
                            if not extracted_name:
                                continue
                            
                            # Skip hidden files (starting with .)
                            if extracted_name.startswith('.'):
                                continue
                            
                            # Skip resource fork files (starting with ._)
                            if extracted_name.startswith('._'):
                                continue
                            
                            # Read the file content
                            extracted_content = zip_ref.read(zip_info.filename)
                            extracted_byte = io.BytesIO(extracted_content)
                            
                            processed_files.append((extracted_byte, extracted_name))
                except zipfile.BadZipFile:
                    # If it's not a valid zip file, treat it as a regular file
                    file_byte.seek(0)
                    processed_files.append((file_byte, file_name))
            else:
                # Regular file, add as-is
                file_byte.seek(0)
                processed_files.append((file_byte, file_name))

        objs = []
        new_paths_full = []
        for file_byte, file_name in processed_files:
            try:
                with sandbox.vol.batch_upload() as batch:
                    data_source_id = uuid.uuid4()
                    objs.append(DataSourceBase(
                        id=data_source_id,
                        user_id=self.user_id,
                        type="file",
                        name=file_name,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ).model_dump())
                    new_path = f"/{mount_group.python_package_name}/data/{file_name}"
                    batch.put_file(file_byte, new_path)
                    new_path_full = Path("/app") / new_path.lstrip("/")
                    new_paths_full.append(new_path_full)
            except FileExistsError:
                pass

        await execute(
            insert(data_source).values(objs),
            commit_after=True
        )

        # Need to reload for the files to appear in the volume
        await sandbox.reload_container()
        return [DataSource(**obj) for obj in objs], new_paths_full

    async def get_data_source_details_submission_code(self) -> Tuple[str, str]:
        if not self.bearer_token:
            raise ValueError(
                "bearer_token is required for data source details submission")

        bearer_token_value = self.bearer_token
        api_url_value = API_URL

        submission_code = (
            f"import requests\n"
            f"import json\n"
            f"\n"
            f"# Submit data source details to the API\n"
            f'url = "{api_url_value}/data-sources/data-source-details"\n'
            f"headers = {{\n"
            f'    "Authorization": "Bearer {bearer_token_value}",\n'
            f'    "Content-Type": "application/json"\n'
            f"}}\n"
            f"\n"
            f"# The data_source_details_dict should be a dictionary following the DataSourceDetailsCreate schema\n"
            f"# It must include:\n"
            f"# - 'data_source_id': UUID of the existing data source\n"
            f"# - 'type_fields': Dictionary with type-specific fields (e.g., file metadata, schema information)\n"
            f"\n"
            f"response = requests.post(url, headers=headers, json=data_source_details_dict)\n"
            f"response.raise_for_status()\n"
            f"result = response.json()\n"
            f"print(json.dumps(result, default=str))\n"
        )

        submission_description = (
            "The submission code expects a variable named 'data_source_details_dict' that contains a dictionary\n"
            "following the DataSourceDetailsCreate schema. This dictionary must include:\n"
            "- 'data_source_id': The UUID of the existing data source (must be provided in the prompt)\n"
            "- 'type_fields': A dictionary containing type-specific fields for the data source\n"
            "\n"
            "For file data sources, type_fields should include fields like:\n"
            "- 'file_name': Name of the file\n"
            "- 'file_path': Absolute path to the file\n"
            "- 'file_type': Type/extension of the file\n"
            "- 'file_size_bytes': Size of the file in bytes\n"
            "- Additional fields like 'json_schema', 'pandas_df_info', 'pandas_df_head', etc. for tabular files\n"
            "\n"
            "The code will POST this dictionary to the API endpoint and print the response.\n"
        )

        return submission_code, submission_description


# For dependency injection
async def get_data_sources_service(user: Annotated[User, Depends(get_current_user)]) -> DataSourceInterface:
    return DataSources(user.id)
