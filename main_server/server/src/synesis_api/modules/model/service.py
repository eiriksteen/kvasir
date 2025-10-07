import uuid
import jsonschema
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, insert, update, delete, func, and_
from fastapi import HTTPException

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.model.models import (
    model,
    model_definition,
    model_entity,
    model_function,
    model_function_input_object_group_definition,
    model_function_output_object_group_definition
)
from synesis_schemas.main_server import (
    ModelInDB,
    ModelFunctionInDB,
    ModelCreate,
    ModelEntityWithModelDef,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntityConfigUpdate,
    ModelDefinitionInDB,
    ModelFull,
    ModelUpdateCreate,
    ModelFunctionFull,
    ModelFunctionInputObjectGroupDefinitionInDB,
    ModelFunctionOutputObjectGroupDefinitionInDB,
)
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.project.service import get_model_entity_ids_in_project


async def create_model(user_id: uuid.UUID, model_create: ModelCreate) -> ModelFull:

    model_definition_obj = ModelDefinitionInDB(
        id=uuid.uuid4(),
        **model_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    embedding = (await embed([f"{model_create.name}: {model_create.description}"]))[0]

    training_function_obj = ModelFunctionInDB(
        id=uuid.uuid4(),
        **model_create.training_function.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    inference_function_obj = ModelFunctionInDB(
        id=uuid.uuid4(),
        **model_create.inference_function.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    model_obj = ModelInDB(
        id=uuid.uuid4(),
        **model_create.model_dump(),
        definition_id=model_definition_obj.id,
        version=1,
        newest_update_description="First version",
        user_id=user_id,
        training_function_id=training_function_obj.id,
        inference_function_id=inference_function_obj.id,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(model_definition).values(**model_definition_obj.model_dump()), commit_after=True)
    await execute(insert(model_function).values(**training_function_obj.model_dump()), commit_after=True)
    await execute(insert(model_function).values(**inference_function_obj.model_dump()), commit_after=True)
    await execute(insert(model).values(**model_obj.model_dump()), commit_after=True)

    training_input_records = [
        ModelFunctionInputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=training_function_obj.id,
            **input_group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input_group in model_create.training_function.input_object_groups
    ]

    training_output_object_records = [
        ModelFunctionOutputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=training_function_obj.id,
            **output_group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output_group in model_create.training_function.output_object_groups
    ]

    inference_input_records = [
        ModelFunctionInputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=inference_function_obj.id,
            **input_group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input_group in model_create.inference_function.input_object_groups
    ]

    inference_output_object_records = [
        ModelFunctionOutputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=inference_function_obj.id,
            **output_group.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output_group in model_create.inference_function.output_object_groups
    ]

    all_input_records = training_input_records + inference_input_records
    if all_input_records:
        await execute(insert(model_function_input_object_group_definition).values(all_input_records), commit_after=True)

    all_output_object_records = training_output_object_records + \
        inference_output_object_records
    if all_output_object_records:
        await execute(insert(model_function_output_object_group_definition).values(all_output_object_records), commit_after=True)

    training_function_full = ModelFunctionFull(
        **training_function_obj.model_dump(),
        input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
            **i) for i in training_input_records],
        output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
            **o) for o in training_output_object_records],

    )

    inference_function_full = ModelFunctionFull(
        **inference_function_obj.model_dump(),
        input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
            **i) for i in inference_input_records],
        output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
            **o) for o in inference_output_object_records],

    )

    return ModelFull(
        **{k: v for k, v in model_obj.model_dump().items() if k != 'embedding'},
        definition=model_definition_obj,
        training_function=training_function_full,
        inference_function=inference_function_full
    )


async def update_model(user_id: uuid.UUID, model_update: ModelUpdateCreate) -> ModelFull:
    max_version_subquery = select(func.max(model.c.version)).where(
        model.c.definition_id == model_update.definition_id)
    existing_model = await fetch_one(select(model).where(and_(model.c.definition_id == model_update.definition_id,
                                                              model.c.version == max_version_subquery)))

    if model_update.updated_description:
        embedding = (await embed([f"{existing_model['filename']}: {model_update.updated_description}"]))[0]
    else:
        embedding = existing_model["embedding"]

    existing_training_function = await fetch_one(
        select(model_function).where(model_function.c.id ==
                                     existing_model["training_function_id"])
    )
    existing_inference_function = await fetch_one(
        select(model_function).where(model_function.c.id ==
                                     existing_model["inference_function_id"])
    )

    if model_update.updated_training_function:
        training_function_obj = ModelFunctionInDB(
            id=uuid.uuid4(),
            docstring=model_update.updated_training_function.docstring if model_update.updated_training_function.docstring else existing_training_function[
                "docstring"],
            args_schema=model_update.updated_training_function.args_schema if model_update.updated_training_function.args_schema else existing_training_function[
                "args_schema"],
            default_args=model_update.updated_training_function.default_args if model_update.updated_training_function.default_args else existing_training_function[
                "default_args"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(model_function).values(**training_function_obj.model_dump()), commit_after=True)
        training_function_id = training_function_obj.id
    else:
        training_function_id = existing_model["training_function_id"]

    if model_update.updated_inference_function:
        inference_function_obj = ModelFunctionInDB(
            id=uuid.uuid4(),
            docstring=model_update.updated_inference_function.docstring if model_update.updated_inference_function.docstring else existing_inference_function[
                "docstring"],
            args_schema=model_update.updated_inference_function.args_schema if model_update.updated_inference_function.args_schema else existing_inference_function[
                "args_schema"],
            default_args=model_update.updated_inference_function.default_args if model_update.updated_inference_function.default_args else existing_inference_function[
                "default_args"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(model_function).values(**inference_function_obj.model_dump()), commit_after=True)
        inference_function_id = inference_function_obj.id
    else:
        inference_function_id = existing_model["inference_function_id"]

    model_obj = ModelInDB(
        id=uuid.uuid4(),
        definition_id=model_update.definition_id,
        python_class_name=model_update.updated_python_class_name if model_update.updated_python_class_name else existing_model[
            "python_class_name"],
        version=existing_model["version"] + 1,
        filename=model_update.updated_filename if model_update.updated_filename else existing_model[
            "filename"],
        description=model_update.updated_description if model_update.updated_description else existing_model[
            "description"],
        newest_update_description=model_update.updates_made_description,
        user_id=user_id,
        source_id=existing_model["source_id"],
        programming_language_with_version=existing_model["programming_language_with_version"],
        implementation_script_path=model_update.updated_implementation_script_path if model_update.updated_implementation_script_path else existing_model[
            "implementation_script_path"],
        setup_script_path=model_update.updated_setup_script_path if model_update.updated_setup_script_path else existing_model[
            "setup_script_path"],
        model_class_docstring=model_update.updated_model_class_docstring if model_update.updated_model_class_docstring else existing_model[
            "model_class_docstring"],
        default_config=model_update.updated_default_config if model_update.updated_default_config else existing_model[
            "default_config"],
        config_schema=model_update.updated_config_schema if model_update.updated_config_schema else existing_model[
            "config_schema"],
        training_function_id=training_function_id,
        inference_function_id=inference_function_id,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(model).values(**model_obj.model_dump()), commit_after=True)

    # Handle training function updates
    if model_update.updated_training_function:
        if model_update.updated_training_function.input_object_groups_to_add:
            training_input_records = [
                ModelFunctionInputObjectGroupDefinitionInDB(
                    id=uuid.uuid4(),
                    function_id=training_function_id,
                    **input_group.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ).model_dump() for input_group in model_update.updated_training_function.input_object_groups_to_add
            ]
            await execute(insert(model_function_input_object_group_definition).values(training_input_records), commit_after=True)

        if model_update.updated_training_function.output_object_group_definitions_to_add:
            training_output_records = [
                ModelFunctionOutputObjectGroupDefinitionInDB(
                    id=uuid.uuid4(),
                    function_id=training_function_id,
                    **output_group.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ).model_dump() for output_group in model_update.updated_training_function.output_object_group_definitions_to_add
            ]
            await execute(insert(model_function_output_object_group_definition).values(training_output_records), commit_after=True)

        if model_update.updated_training_function.input_object_groups_to_remove:
            await execute(delete(model_function_input_object_group_definition).where(
                model_function_input_object_group_definition.c.id.in_(
                    model_update.updated_training_function.input_object_groups_to_remove)
            ), commit_after=True)

        if model_update.updated_training_function.output_object_group_definitions_to_remove:
            await execute(delete(model_function_output_object_group_definition).where(
                model_function_output_object_group_definition.c.id.in_(
                    model_update.updated_training_function.output_object_group_definitions_to_remove)
            ), commit_after=True)

    # Handle inference function updates
    if model_update.updated_inference_function:
        if model_update.updated_inference_function.input_object_groups_to_add:
            inference_input_records = [
                ModelFunctionInputObjectGroupDefinitionInDB(
                    id=uuid.uuid4(),
                    function_id=inference_function_id,
                    **input_group.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ).model_dump() for input_group in model_update.updated_inference_function.input_object_groups_to_add
            ]
            await execute(insert(model_function_input_object_group_definition).values(inference_input_records), commit_after=True)

        if model_update.updated_inference_function.output_object_group_definitions_to_add:
            inference_output_records = [
                ModelFunctionOutputObjectGroupDefinitionInDB(
                    id=uuid.uuid4(),
                    function_id=inference_function_id,
                    **output_group.model_dump(),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ).model_dump() for output_group in model_update.updated_inference_function.output_object_group_definitions_to_add
            ]
            await execute(insert(model_function_output_object_group_definition).values(inference_output_records), commit_after=True)

        if model_update.updated_inference_function.input_object_groups_to_remove:
            await execute(delete(model_function_input_object_group_definition).where(
                model_function_input_object_group_definition.c.id.in_(
                    model_update.updated_inference_function.input_object_groups_to_remove)
            ), commit_after=True)

        if model_update.updated_inference_function.output_object_group_definitions_to_remove:
            await execute(delete(model_function_output_object_group_definition).where(
                model_function_output_object_group_definition.c.id.in_(
                    model_update.updated_inference_function.output_object_group_definitions_to_remove)
            ), commit_after=True)

    return (await get_models([model_obj.id]))[0]


async def get_models(model_ids: List[uuid.UUID]) -> List[ModelFull]:

    model_query = select(model).where(model.c.id.in_(model_ids))
    models = await fetch_all(model_query)

    model_definition_query = select(model_definition).where(
        model_definition.c.id.in_([m["definition_id"] for m in models]))
    model_definition_records = await fetch_all(model_definition_query)

    # Get all function IDs
    function_ids = []
    for m in models:
        function_ids.append(m["training_function_id"])
        function_ids.append(m["inference_function_id"])

    # Query function records
    function_query = select(model_function).where(
        model_function.c.id.in_(function_ids))
    function_records = await fetch_all(function_query)

    # Query input/output definitions by function_id
    input_object_group_definition_query = select(model_function_input_object_group_definition).where(
        model_function_input_object_group_definition.c.function_id.in_(function_ids))
    all_input_object_group_definition_records = await fetch_all(input_object_group_definition_query)

    output_object_group_definition_query = select(model_function_output_object_group_definition).where(
        model_function_output_object_group_definition.c.function_id.in_(function_ids))
    all_output_object_group_definition_records = await fetch_all(output_object_group_definition_query)

    output_objs = []
    for model_id in model_ids:
        model_record = next(m for m in models if m["id"] == model_id)
        model_definition_record = next(
            m for m in model_definition_records if m["id"] == model_record["definition_id"])

        # Get function records for this model
        training_function_record = next(
            f for f in function_records if f["id"] == model_record["training_function_id"])
        inference_function_record = next(
            f for f in function_records if f["id"] == model_record["inference_function_id"])

        # Filter input/output definitions by function_id
        training_input_records = [
            i for i in all_input_object_group_definition_records
            if i["function_id"] == model_record["training_function_id"]
        ]
        training_output_object_records = [
            o for o in all_output_object_group_definition_records
            if o["function_id"] == model_record["training_function_id"]
        ]

        inference_input_records = [
            i for i in all_input_object_group_definition_records
            if i["function_id"] == model_record["inference_function_id"]
        ]
        inference_output_object_records = [
            o for o in all_output_object_group_definition_records
            if o["function_id"] == model_record["inference_function_id"]
        ]

        # Build ModelFunctionFull objects
        training_function_full = ModelFunctionFull(
            **training_function_record,
            input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
                **i) for i in training_input_records],
            output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
                **o) for o in training_output_object_records],
        )

        inference_function_full = ModelFunctionFull(
            **inference_function_record,
            input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
                **i) for i in inference_input_records],
            output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
                **o) for o in inference_output_object_records],
        )

        # Build ModelFull object (excluding embedding)
        output_objs.append(
            ModelFull(
                **{k: v for k, v in model_record.items() if k != 'embedding'},
                definition=ModelDefinitionInDB(**model_definition_record),
                training_function=training_function_full,
                inference_function=inference_function_full
            )
        )

    return output_objs


async def create_model_entity(user_id: uuid.UUID, model_entity_create: ModelEntityCreate) -> ModelEntityInDB:
    model_entity_obj = ModelEntityInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **model_entity_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await execute(insert(model_entity).values(**model_entity_obj.model_dump()), commit_after=True)

    return model_entity_obj


async def get_user_model_entities_by_ids(user_id: uuid.UUID, model_entity_ids: List[uuid.UUID]) -> List[ModelEntityWithModelDef]:
    model_entity_query = select(model_entity).where(
        model_entity.c.id.in_(model_entity_ids)
    ).where(model_entity.c.user_id == user_id)
    model_entity_records = await fetch_all(model_entity_query)

    model_ids = [e["model_id"] for e in model_entity_records]
    models_full = await get_models(model_ids)

    model_entity_full_objs = []
    for entity_id in model_entity_ids:
        model_entity_record = next(
            (e for e in model_entity_records if e["id"] == entity_id), None)

        if model_entity_record is not None:
            model_full = next(
                (m for m in models_full if m.id == model_entity_record["model_id"]), None)

            if model_full is not None:
                model_entity_full_objs.append(ModelEntityWithModelDef(
                    **model_entity_record,
                    model=model_full)
                )

    return model_entity_full_objs


async def get_project_model_entities(user_id: uuid.UUID, project_id: uuid.UUID) -> List[ModelEntityWithModelDef]:
    model_ids = await get_model_entity_ids_in_project(project_id)
    model_entities = await get_user_model_entities_by_ids(user_id, model_ids)
    return model_entities


async def set_new_model_entity_config(user_id: uuid.UUID, model_entity_id: uuid.UUID, model_entity_config_update: ModelEntityConfigUpdate) -> ModelEntityInDB:
    model_entity_obj = (await get_user_model_entities_by_ids(user_id, [model_entity_id]))[0]

    is_fitted = model_entity_obj.weights_save_dir is not None
    if is_fitted:
        raise HTTPException(
            status_code=400, detail="Model entity is fitted and the config cannot be updated")

    model_record = await fetch_one(
        select(model).join(model_entity).where(model_entity.c.id == model_entity_id))

    try:
        jsonschema.validate(
            model_entity_config_update.config, model_record["config_schema"])
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid config or args: {e.message}")

    await execute(update(model_entity).where(model_entity.c.id == model_entity_id).values(**model_entity_config_update.model_dump()), commit_after=True)

    model_entity_obj.config = model_entity_config_update.config

    return model_entity_obj
