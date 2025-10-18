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
    model_entity_implementation,
    model_function,
    model_function_input_object_group_definition,
    model_function_output_object_group_definition,
    model_source,
    pypi_model_source
)
from synesis_schemas.main_server import (
    ModelInDB,
    ModelFunctionInDB,
    ModelCreate,
    ModelEntity,
    ModelEntityInDB,
    ModelEntityCreate,
    ModelEntityConfigUpdate,
    ModelDefinitionInDB,
    Model,
    ModelUpdateCreate,
    ModelFunction,
    ModelFunctionInputObjectGroupDefinitionInDB,
    ModelFunctionOutputObjectGroupDefinitionInDB,
    ModelSource,
    PypiModelSourceCreate,
    PypiModelSource,
    ModelSourceCreate,
    ModelSourceInDB,
    PypiModelSourceInDB,
)
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.code.service import create_script, get_scripts
from synesis_api.modules.model.description import get_model_entity_description, get_model_description


async def create_model(user_id: uuid.UUID, model_create: ModelCreate) -> Model:

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

    implementation_script_obj = await create_script(user_id, model_create.implementation_script_create)

    if model_create.setup_script_create:
        setup_script_obj = await create_script(user_id, model_create.setup_script_create)
    else:
        setup_script_obj = None

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
        implementation_script_id=implementation_script_obj.id,
        setup_script_id=setup_script_obj.id if setup_script_obj else None,
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

    training_function_full = ModelFunction(
        **training_function_obj.model_dump(),
        input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
            **i) for i in training_input_records],
        output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
            **o) for o in training_output_object_records],

    )

    inference_function_full = ModelFunction(
        **inference_function_obj.model_dump(),
        input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
            **i) for i in inference_input_records],
        output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
            **o) for o in inference_output_object_records],

    )

    return Model(
        **{k: v for k, v in model_obj.model_dump().items() if k != 'embedding'},
        definition=model_definition_obj,
        training_function=training_function_full,
        inference_function=inference_function_full,
        implementation_script=implementation_script_obj,
        setup_script=setup_script_obj
    )


async def update_model(user_id: uuid.UUID, model_update: ModelUpdateCreate) -> Model:
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

    # update script

    implementation_script_obj = await create_script(user_id, model_update.new_implementation_create)
    if model_update.new_setup_create:
        setup_script_obj = await create_script(user_id, model_update.new_setup_create)
    else:
        setup_script_obj = None

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
        implementation_script_id=implementation_script_obj.id,
        setup_script_id=setup_script_obj.id if setup_script_obj else existing_model[
            "setup_script_id"],
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

    # Handle model entities updates
    if model_update.model_entities_to_update:
        await execute(
            update(model_entity_implementation).where(model_entity_implementation.c.id.in_(
                model_update.model_entities_to_update)).values(model_id=model_obj.id), commit_after=True)

    return (await get_models([model_obj.id]))[0]


async def get_models(model_ids: List[uuid.UUID]) -> List[Model]:

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

    # Query script records
    implementation_script_records = await get_scripts(m["implementation_script_id"] for m in models)
    setup_script_records = await get_scripts(m["setup_script_id"] for m in models if m["setup_script_id"])

    output_objs = []
    for model_id in model_ids:
        model_obj = ModelInDB(**next(m for m in models if m["id"] == model_id))
        model_definition_obj = ModelDefinitionInDB(**next(
            m for m in model_definition_records if m["id"] == model_obj.definition_id))

        # Get function records for this model
        training_function_record = next(
            f for f in function_records if f["id"] == model_obj.training_function_id)
        inference_function_record = next(
            f for f in function_records if f["id"] == model_obj.inference_function_id)

        # Filter input/output definitions by function_id
        training_input_records = [
            i for i in all_input_object_group_definition_records
            if i["function_id"] == model_obj.training_function_id
        ]
        training_output_object_records = [
            o for o in all_output_object_group_definition_records
            if o["function_id"] == model_obj.training_function_id
        ]

        inference_input_records = [
            i for i in all_input_object_group_definition_records
            if i["function_id"] == model_obj.inference_function_id
        ]
        inference_output_object_records = [
            o for o in all_output_object_group_definition_records
            if o["function_id"] == model_obj.inference_function_id
        ]

        # Build ModelFunction objects
        training_function_obj = ModelFunctionInDB(
            **training_function_record,
            input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
                **i) for i in training_input_records],
            output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
                **o) for o in training_output_object_records],
        )

        inference_function_obj = ModelFunctionInDB(
            **inference_function_record,
            input_object_groups=[ModelFunctionInputObjectGroupDefinitionInDB(
                **i) for i in inference_input_records],
            output_object_groups=[ModelFunctionOutputObjectGroupDefinitionInDB(
                **o) for o in inference_output_object_records],
        )

        # Get script records for this model
        implementation_script_obj = next(
            s for s in implementation_script_records if s.id == model_obj.implementation_script_id)
        setup_script_obj = next(
            (s for s in setup_script_records if s.id == model_obj.setup_script_id))

        model_description = get_model_description(
            model_obj, model_definition_obj, training_function_obj, inference_function_obj, implementation_script_obj, setup_script_obj)

        # Build Model object (excluding embedding)
        output_objs.append(
            Model(
                **model_obj.model_dump(),
                definition=model_definition_obj,
                training_function=training_function_obj,
                inference_function=inference_function_obj,
                implementation_script=implementation_script_obj,
                setup_script=setup_script_obj,
                description_for_agent=model_description
            )
        )

    return output_objs


async def create_model_entity(user_id: uuid.UUID, model_entity_create: ModelEntityCreate) -> ModelEntityInDB:

    config_schema = await fetch_one(select(model.c.config_schema).where(model.c.id == model_entity_create.model_id))

    try:
        jsonschema.validate(model_entity_create.config,
                            config_schema["config_schema"])
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid config: {e.message}, schema: {config_schema['config_schema']}")

    model_entity_obj = ModelEntityInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        **model_entity_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await execute(insert(model_entity_implementation).values(**model_entity_obj.model_dump()), commit_after=True)

    return model_entity_obj


async def get_user_model_entities(user_id: uuid.UUID, model_entity_ids: List[uuid.UUID]) -> List[ModelEntity]:
    model_entity_query = select(model_entity_implementation).where(
        model_entity_implementation.c.id.in_(model_entity_ids)
    ).where(model_entity_implementation.c.user_id == user_id)
    model_entity_records = await fetch_all(model_entity_query)

    model_ids = [e["model_id"] for e in model_entity_records]
    models_objs = await get_models(model_ids)

    model_entity_full_objs = []
    for entity_id in model_entity_ids:
        model_entity_record = next(
            (e for e in model_entity_records if e["id"] == entity_id), None)

        if model_entity_record is None:
            raise HTTPException(
                status_code=404, detail="Model entity not found")

        model_obj = next(
            (m for m in models_objs if m.id == model_entity_record["model_id"]), None)

        if model_obj is None:
            raise HTTPException(
                status_code=404, detail="Model not found")

        model_entity_obj = ModelEntityInDB(
            **model_entity_record, model=model_obj)

        description = get_model_entity_description(model_entity_obj, model_obj)

        model_entity_full_objs.append(ModelEntity(
            **model_entity_record,
            model=model_obj,
            description_for_agent=description
        ))

    return model_entity_full_objs


async def set_new_model_entity_config(user_id: uuid.UUID, model_entity_id: uuid.UUID, model_entity_config_update: ModelEntityConfigUpdate) -> ModelEntityInDB:
    model_entity_obj = (await get_user_model_entities(user_id, [model_entity_id]))[0]

    is_fitted = model_entity_obj.weights_save_dir is not None
    if is_fitted:
        raise HTTPException(
            status_code=400, detail="Model entity is fitted and the config cannot be updated")

    model_record = await fetch_one(
        select(model).join(model_entity_implementation).where(model_entity_implementation.c.id == model_entity_id))

    try:
        jsonschema.validate(
            model_entity_config_update.config, model_record["config_schema"])
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid config or args: {e.message}")

    await execute(update(model_entity_implementation).where(model_entity_implementation.c.id == model_entity_id).values(**model_entity_config_update.model_dump()), commit_after=True)

    model_entity_obj.config = model_entity_config_update.config

    return model_entity_obj


async def create_model_source(user_id: uuid.UUID, model_source_create: ModelSourceCreate) -> ModelSource:

    # Check if source with the data exists:
    if type(model_source_create) == PypiModelSourceCreate:
        pypi_model_source_query = select(pypi_model_source.c.id).where(
            pypi_model_source.c.package_name == model_source_create.package_name,
            pypi_model_source.c.package_version == model_source_create.package_version,
        )
        pypi_model_source_record = await fetch_all(pypi_model_source_query)
        fetched_ids = [record["id"] for record in pypi_model_source_record]
        public_or_user_owned_results = (await get_user_or_public_model_sources_by_ids(user_id, fetched_ids))
        if public_or_user_owned_results:
            return public_or_user_owned_results[0]

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

        output_obj = PypiModelSource(
            **model_source_record.model_dump(),
            package_name=pypi_model_source_record.package_name,
            package_version=pypi_model_source_record.package_version
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
            output_objs.append(PypiModelSource(
                **base_obj.model_dump(),
                package_name=pypi_model_source_record.package_name,
                package_version=pypi_model_source_record.package_version
            ))
        # elif: ... etc

    return output_objs


async def get_model_sources_by_ids(user_id: uuid.UUID, model_source_ids: List[uuid.UUID]) -> List[ModelSource]:
    records = await get_user_or_public_model_sources_by_ids(user_id, model_source_ids)
    return records
