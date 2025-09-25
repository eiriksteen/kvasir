import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, insert

from synesis_api.database.service import fetch_all, execute
from synesis_api.modules.model.models import model, model_entity
from synesis_schemas.main_server import ModelInDB, ModelCreate, ModelEntityFull, ModelEntityInDB, ModelEntityCreate, ModelFull
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.project.service import get_model_entity_ids_in_project
from synesis_api.modules.function.service import get_functions


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
        name=model_entity_create.name,
        description=model_entity_create.description,
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
    model_entity_records = await fetch_all(model_entity_query)

    model_query = select(model).where(
        model.c.id.in_([e["model_id"] for e in model_entity_records]))
    model_records = await fetch_all(model_query)

    function_objs = await get_functions(
        [e["inference_function_id"] for e in model_records] +
        [e["training_function_id"] for e in model_records]
    )

    model_entity_full_objs = []
    for entity_id in model_entity_ids:
        model_entity_record = next(
            (e for e in model_entity_records if e["id"] == entity_id), None)
        model_record = next(
            (m for m in model_records if m["id"] == model_entity_record["model_id"]), None)
        inference_function = next(
            (f for f in function_objs if f.id == model_record["inference_function_id"]), None)
        training_function = next(
            (f for f in function_objs if f.id == model_record["training_function_id"]), None)
        if model_entity_record is not None and model_record is not None:
            model_entity_full_objs.append(ModelEntityFull(
                **model_entity_record,
                model=ModelFull(
                    **model_record,
                    inference_function=inference_function,
                    training_function=training_function)
            ))

    return model_entity_full_objs


async def get_project_model_entities(project_id: uuid.UUID) -> List[ModelEntityFull]:
    model_ids = await get_model_entity_ids_in_project(project_id)
    model_entities = await get_user_model_entities_by_ids(model_ids)
    return model_entities
