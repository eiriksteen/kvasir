import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, insert

from synesis_api.database.service import fetch_all, execute
from synesis_api.modules.model.models import model, model_entity
from synesis_schemas.main_server import ModelInDB, ModelCreate, ModelEntityFull, ModelEntityInDB, ModelEntityCreate
from synesis_api.utils.rag_utils import embed


async def create_model(user_id: uuid.UUID, model_create: ModelCreate) -> ModelInDB:

    embedding = (await embed([f"{model_create.name}: {model_create.description}"]))[0]

    model_obj = ModelInDB(
        id=uuid.uuid4(),
        owner_id=user_id,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **model_create.model_dump(),
    )

    await execute(insert(model).values(**model_obj.model_dump()), commit_after=True)

    return model_obj


async def create_model_entity(model_entity_create: ModelEntityCreate) -> ModelEntityInDB:
    model_entity_obj = ModelEntityInDB(
        id=uuid.uuid4(),
        model_id=model_entity_create.model_id,
        project_id=model_entity_create.project_id,
        weights_save_dir=model_entity_create.weights_save_dir,
        pipeline_id=model_entity_create.pipeline_id,
        config=model_entity_create.config,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await execute(insert(model_entity).values(**model_entity_obj.model_dump()), commit_after=True)

    return model_entity_obj


async def get_user_model_entities_by_ids(model_entity_ids: List[uuid.UUID]) -> List[ModelEntityFull]:
    model_entity_query = select(model_entity).where(
        model_entity.c.id.in_(model_entity_ids))
    results = await fetch_all(model_entity_query)
    model_query = select(model).where(
        model.c.id.in_([e["model_id"] for e in results]))
    models = await fetch_all(model_query)

    model_entity_records = []
    for entity_id in model_entity_ids:
        model_entity_record = next(
            (e for e in results if e["id"] == entity_id), None)
        model_record = next(
            (m for m in models if m["id"] == model_entity_record["model_id"]), None)
        if model_entity_record is not None and model_record is not None:
            model_entity_records.append(ModelEntityFull(
                **model_entity_record, model=ModelInDB(**model_record)))
    return model_entity_records
