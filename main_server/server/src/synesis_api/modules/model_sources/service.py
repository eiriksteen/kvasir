import uuid
from typing import List
from sqlalchemy import insert, select
from datetime import datetime
from synesis_schemas.main_server import ModelSourceInDB, ModelSourceCreate, PypiModelSourceInDB, PypiModelSourceCreate, ModelSource, PypiModelSourceFull

from synesis_api.modules.model_sources.models import model_source, pypi_model_source
from synesis_api.database.service import execute, fetch_one, fetch_all
from synesis_api.utils.rag_utils import embed


async def create_model_source(user_id: uuid.UUID, model_source_create: ModelSourceCreate) -> ModelSource:

    embedding = (await embed([f"{model_source_create.name}: {model_source_create.description}"]))[0]

    model_source_record = ModelSourceInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        type=model_source_create.type,
        name=model_source_create.name,
        description=model_source_create.description,
        public=model_source_create.public,
        embedding=embedding,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    await execute(insert(model_source).values(model_source_record.model_dump()), commit_after=True)

    output_obj = None
    if type(model_source_create) == PypiModelSourceCreate:
        pypi_model_source_record = PypiModelSourceInDB(
            id=model_source_record.id,
            model_source_id=model_source_record.id,
            package_name=model_source_create.package_name,
            package_version=model_source_create.package_version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        await execute(insert(pypi_model_source).values(pypi_model_source_record.model_dump()), commit_after=True)

        output_obj = PypiModelSourceFull(
            **model_source_record.model_dump(),
            **pypi_model_source_record.model_dump()
        )

    # TODO: Add more model source types with elifs here

    return output_obj


async def get_user_or_public_model_sources_by_ids(user_id: uuid.UUID, model_source_ids: List[uuid.UUID]) -> List[ModelSource]:

    # Get the base records

    user_model_source_query = select(model_source).where(
        model_source.c.user_id == user_id,
        model_source.c.id.in_(model_source_ids)
    )

    user_model_source_records = await fetch_all(user_model_source_query)

    public_model_source_query = select(model_source).where(
        model_source.c.public == True,
        model_source.c.id.in_(model_source_ids)
    )

    public_model_source_records = await fetch_all(public_model_source_query)

    all_model_source_records = user_model_source_records + public_model_source_records

    # Then get the detailed records

    pypi_source_ids = [record["id"]
                       for record in all_model_source_records if record["type"] == "pypi"]

    # github_source_ids = ... etc

    pypi_model_source_query = select(pypi_model_source).where(
        pypi_model_source.c.id.in_(pypi_source_ids))

    pypi_model_source_records = await fetch_all(pypi_model_source_query)

    output_objs = []
    for source_id in model_source_ids:
        base_obj = ModelSourceInDB(
            **next(record for record in all_model_source_records if record["id"] == source_id))
        if source_id in pypi_source_ids:
            pypi_model_source_record = PypiModelSourceInDB(
                **next(record for record in pypi_model_source_records if record["id"] == source_id))
            output_objs.append(PypiModelSourceFull(
                **base_obj.model_dump(), **pypi_model_source_record.model_dump()))
        # elif: ... etc

    return output_objs


async def get_model_source_by_id(user_id: uuid.UUID, model_source_id: uuid.UUID) -> ModelSource:
    records = await get_user_or_public_model_sources_by_ids(user_id, [model_source_id])
    return records[0]
