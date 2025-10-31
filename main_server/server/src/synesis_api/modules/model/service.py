import uuid
import jsonschema
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, insert, update, func, and_
from fastapi import HTTPException

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.model.models import (
    model_implementation,
    model_definition,
    model_entity,
    model_entity_implementation,
    model_function,
    model_source,
    pypi_model_source
)
from synesis_schemas.main_server import (
    ModelImplementationInDB,
    ModelFunctionInDB,
    ModelImplementationCreate,
    ModelEntity,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntityConfigUpdate,
    ModelDefinitionInDB,
    ModelEntityImplementationInDB,
    ModelEntityImplementationCreate,
    ModelEntityImplementation,
    ModelImplementation,
    ModelUpdateCreate,
    ModelSource,
    ModelSourceCreate,
    ModelSourceInDB,
    PypiModelSourceInDB,
)
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.model.description import get_model_entity_description, get_model_description


async def create_model(user_id: uuid.UUID, model_create: ModelImplementationCreate) -> ModelImplementation:

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

    model_source_obj = await create_model_source(model_create.source)

    model_obj = ModelImplementationInDB(
        id=uuid.uuid4(),
        source_id=model_source_obj.id,
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
    await execute(insert(model_implementation).values(**model_obj.model_dump()), commit_after=True)

    training_function_full = ModelFunctionInDB(
        **training_function_obj.model_dump()
    )

    inference_function_full = ModelFunctionInDB(
        **inference_function_obj.model_dump()
    )

    description = get_model_description(
        model_obj, model_definition_obj, training_function_full, inference_function_full, model_obj.implementation_script_path, model_obj.setup_script_path
    )

    return ModelImplementation(
        **{k: v for k, v in model_obj.model_dump().items() if k != 'embedding'},
        definition=model_definition_obj,
        training_function=training_function_full,
        inference_function=inference_function_full,
        description_for_agent=description
    )


async def update_model(user_id: uuid.UUID, model_update: ModelUpdateCreate) -> ModelImplementation:
    max_version_subquery = select(func.max(model_implementation.c.version)).where(
        model_implementation.c.definition_id == model_update.definition_id)
    existing_model = await fetch_one(select(model_implementation).where(and_(model_implementation.c.definition_id == model_update.definition_id,
                                                                             model_implementation.c.version == max_version_subquery)))

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

    # update script
    implementation_script_path = model_update.new_implementation_script_path
    setup_script_path = model_update.new_setup_script_path if model_update.new_setup_script_path else existing_model.get(
        "setup_script_path")

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

    model_obj = ModelImplementationInDB(
        id=uuid.uuid4(),
        implementation_script_path=implementation_script_path,
        setup_script_path=setup_script_path,
        definition_id=model_update.definition_id,
        python_class_name=model_update.updated_python_class_name if model_update.updated_python_class_name else existing_model[
            "python_class_name"],
        version=existing_model["version"] + 1,
        description=model_update.updated_description if model_update.updated_description else existing_model[
            "description"],
        newest_update_description=model_update.updates_made_description,
        user_id=user_id,
        source_id=existing_model["source_id"],
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

    await execute(insert(model_implementation).values(**model_obj.model_dump()), commit_after=True)

    # Handle training function updates
    if model_update.updated_training_function:
        await execute(update(model_function).where(model_function.c.id == training_function_id).values(**model_update.updated_training_function.model_dump()), commit_after=True)

    # Handle inference function updates
    if model_update.updated_inference_function:
        await execute(update(model_function).where(model_function.c.id == inference_function_id).values(**model_update.updated_inference_function.model_dump()), commit_after=True)

    # Handle model entities updates
    if model_update.model_entities_to_update:
        await execute(
            update(model_entity_implementation).where(model_entity_implementation.c.id.in_(
                model_update.model_entities_to_update)).values(model_id=model_obj.id), commit_after=True)

    return (await get_models([model_obj.id]))[0]


async def get_models(model_ids: List[uuid.UUID]) -> List[ModelImplementation]:

    model_query = select(model_implementation).where(
        model_implementation.c.id.in_(model_ids))
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

    output_objs = []
    for model_id in model_ids:
        model_obj = ModelImplementationInDB(
            **next(m for m in models if m["id"] == model_id))
        model_definition_obj = ModelDefinitionInDB(**next(
            m for m in model_definition_records if m["id"] == model_obj.definition_id))

        # Get function records for this model
        training_function_record = next(
            f for f in function_records if f["id"] == model_obj.training_function_id)
        inference_function_record = next(
            f for f in function_records if f["id"] == model_obj.inference_function_id)

        # Build ModelFunction objects
        training_function_obj = ModelFunctionInDB(**training_function_record)
        inference_function_obj = ModelFunctionInDB(**inference_function_record)

        model_description = get_model_description(
            model_obj, model_definition_obj, training_function_obj, inference_function_obj, model_obj.implementation_script_path, model_obj.setup_script_path)

        # Build Model object (excluding embedding)
        output_objs.append(
            ModelImplementation(
                **model_obj.model_dump(),
                definition=model_definition_obj,
                training_function=training_function_obj,
                inference_function=inference_function_obj,
                description_for_agent=model_description
            )
        )

    return output_objs


async def create_model_entity(user_id: uuid.UUID, model_entity_create: ModelEntityCreate) -> ModelEntityInDB:
    """
    Create a bare model entity without implementation.
    Used when developing or when the exact implementation hasn't been selected yet.
    """
    model_entity_obj = ModelEntityInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=model_entity_create.name,
        description=model_entity_create.description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await execute(insert(model_entity).values(**model_entity_obj.model_dump()), commit_after=True)
    return model_entity_obj


async def create_model_entity_implementation(user_id: uuid.UUID, model_entity_implementation_create: ModelEntityImplementationCreate) -> ModelEntityInDB:
    """
    Create a model entity with an optional implementation.
    If model_entity_id is provided, use existing entity. Otherwise create new entity.
    If model_implementation_id is provided, create implementation. Otherwise leave bare entity.
    """

    # Handle model entity creation or retrieval
    if model_entity_implementation_create.model_entity_id:
        # Verify entity exists and user owns it
        entity_query = select(model_entity).where(
            model_entity.c.id == model_entity_implementation_create.model_entity_id,
            model_entity.c.user_id == user_id
        )
        entity_record = await fetch_one(entity_query)
        if not entity_record:
            raise HTTPException(
                status_code=404, detail="Model entity not found")
        model_entity_obj = ModelEntityInDB(**entity_record)
    else:
        # Create new model entity
        model_entity_obj = ModelEntityInDB(
            id=uuid.uuid4(),
            user_id=user_id,
            name=model_entity_implementation_create.model_entity_create.name,
            description=model_entity_implementation_create.model_entity_create.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await execute(insert(model_entity).values(**model_entity_obj.model_dump()), commit_after=True)

    # Handle model implementation if provided
    if model_entity_implementation_create.model_implementation_id or model_entity_implementation_create.model_implementation_create:
        # Get or create model implementation
        if model_entity_implementation_create.model_implementation_create:
            model_impl = await create_model(user_id, model_entity_implementation_create.model_implementation_create)
            model_implementation_id = model_impl.id
        else:
            model_implementation_id = model_entity_implementation_create.model_implementation_id

        # Validate config against schema
        config_schema_record = await fetch_one(
            select(model_implementation.c.config_schema).where(
                model_implementation.c.id == model_implementation_id
            )
        )

        try:
            jsonschema.validate(
                model_entity_implementation_create.config,
                config_schema_record["config_schema"]
            )
        except jsonschema.ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid config: {e.message}, schema: {config_schema_record['config_schema']}"
            )

        # Create model entity implementation
        model_entity_implementation_obj = ModelEntityImplementationInDB(
            id=model_entity_obj.id,
            model_id=model_implementation_id,
            config=model_entity_implementation_create.config,
            weights_save_dir=model_entity_implementation_create.weights_save_dir,
            pipeline_id=model_entity_implementation_create.pipeline_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await execute(insert(model_entity_implementation).values(**model_entity_implementation_obj.model_dump()), commit_after=True)

    return model_entity_obj


async def get_user_model_entities(user_id: uuid.UUID, model_entity_ids: List[uuid.UUID]) -> List[ModelEntity]:
    """
    Fetch model entities with optional implementations.
    Returns ModelEntity objects with implementation field populated if available.
    """

    # Fetch base model entities
    model_entity_query = select(model_entity).where(
        model_entity.c.id.in_(model_entity_ids),
        model_entity.c.user_id == user_id
    )
    model_entity_records = await fetch_all(model_entity_query)

    if len(model_entity_records) != len(model_entity_ids):
        raise HTTPException(
            status_code=404, detail="One or more model entities not found")

    # Fetch implementations (may not exist for all entities)
    model_entity_implementation_query = select(model_entity_implementation).where(
        model_entity_implementation.c.id.in_(model_entity_ids)
    )
    model_entity_implementation_records = await fetch_all(model_entity_implementation_query)

    # Fetch model implementations if any implementations exist
    model_implementation_objs = []
    if model_entity_implementation_records:
        model_impl_ids = [e["model_id"]
                          for e in model_entity_implementation_records]
        model_implementation_objs = await get_models(model_impl_ids)

    # Build ModelEntity objects
    model_entity_full_objs = []
    for entity_id in model_entity_ids:
        # Get base entity
        entity_record = next(
            (e for e in model_entity_records if e["id"] == entity_id))
        entity_obj = ModelEntityInDB(**entity_record)

        # Get implementation if exists
        impl_record = next(
            (e for e in model_entity_implementation_records if e["id"] == entity_id), None)

        if impl_record:
            # Entity has implementation
            model_impl_obj = next(
                (m for m in model_implementation_objs if m.id == impl_record["model_id"]))

            entity_implementation_obj = ModelEntityImplementationInDB(
                **impl_record)

            model_entity_impl = ModelEntityImplementation(
                **entity_implementation_obj.model_dump(),
                model_implementation=model_impl_obj
            )

            description = get_model_entity_description(
                entity_obj, model_entity_impl)

            model_entity_full_objs.append(ModelEntity(
                **entity_obj.model_dump(),
                implementation=model_entity_impl,
                description_for_agent=description
            ))
        else:
            # Entity without implementation (bare entity)
            description = f"Model Entity: {entity_obj.name}\n\n{entity_obj.description}\n\n*Note: No implementation selected yet*"

            model_entity_full_objs.append(ModelEntity(
                **entity_obj.model_dump(),
                implementation=None,
                description_for_agent=description
            ))

    return model_entity_full_objs


async def set_new_model_entity_config(user_id: uuid.UUID, model_entity_id: uuid.UUID, model_entity_config_update: ModelEntityConfigUpdate) -> ModelEntityInDB:
    model_entity_obj = (await get_user_model_entities(user_id, [model_entity_id]))[0]

    # Check if entity has implementation
    if not model_entity_obj.implementation:
        raise HTTPException(
            status_code=400, detail="Model entity has no implementation. Cannot update config.")

    # Check if model is already fitted
    is_fitted = model_entity_obj.implementation.weights_save_dir is not None
    if is_fitted:
        raise HTTPException(
            status_code=400, detail="Model entity is fitted and the config cannot be updated")

    # Validate config against schema
    model_record = await fetch_one(
        select(model_implementation).join(model_entity_implementation).where(
            model_entity_implementation.c.id == model_entity_id
        )
    )

    try:
        jsonschema.validate(
            model_entity_config_update.config, model_record["config_schema"])
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid config: {e.message}")

    # Update config
    await execute(
        update(model_entity_implementation).where(
            model_entity_implementation.c.id == model_entity_id
        ).values(**model_entity_config_update.model_dump()),
        commit_after=True
    )

    # Return updated entity
    return (await get_user_model_entities(user_id, [model_entity_id]))[0]


async def create_model_source(model_source_create: ModelSourceCreate) -> ModelSource:
    # Check if source with the data exists:
    if model_source_create.type == "pypi":
        model_source_query = select(model_source, pypi_model_source
                                    ).join(pypi_model_source, model_source.c.id == pypi_model_source.c.id
                                           ).where(pypi_model_source.c.package_name == model_source_create.type_fields.package_name,
                                                   pypi_model_source.c.package_version == model_source_create.type_fields.package_version)

        model_source_record = await fetch_one(model_source_query)

        if model_source_record:
            return ModelSource(
                **model_source_record,
                type_fields=PypiModelSourceInDB(**model_source_record)
            )

    model_source_obj = ModelSourceInDB(
        id=uuid.uuid4(),
        **model_source_create.model_dump(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    type_fields_obj = None
    if model_source_create.type == "pypi":
        type_fields_obj = PypiModelSourceInDB(
            id=model_source_obj.id,
            model_source_id=model_source_obj.id,
            package_name=model_source_create.type_fields.package_name,
            package_version=model_source_create.type_fields.package_version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid model source type: {model_source_create.type}")

    await execute(insert(model_source).values(**model_source_obj.model_dump()), commit_after=True)
    if type_fields_obj:
        await execute(insert(pypi_model_source).values(**type_fields_obj.model_dump()), commit_after=True)

    return ModelSource(**model_source_obj.model_dump(), type_fields=type_fields_obj)
