import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy import insert, select, func, delete
from sqlalchemy import and_

from synesis_api.database.service import execute, fetch_all, fetch_one
from synesis_api.modules.function.models import (
    function,
    function_definition,
    function_input_object_group_definition,
    function_output_object_group_definition
)
from synesis_schemas.main_server import (
    FunctionInDB,
    FunctionCreate,
    FunctionInputObjectGroupDefinitionInDB,
    FunctionOutputObjectGroupDefinitionInDB,
    FunctionDefinitionInDB,
    FunctionUpdateCreate,
    Function,
    FunctionWithoutEmbedding,
)
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.code.service import create_script, get_scripts
from synesis_api.modules.function.description import get_function_description


async def create_function(user_id: uuid.UUID, function_create: FunctionCreate) -> Function:

    implementation_script_obj = await create_script(user_id, function_create.implementation_script_create)
    if function_create.setup_script_create:
        setup_script_obj = await create_script(user_id, function_create.setup_script_create)
    else:
        setup_script_obj = None

    function_definition_obj = FunctionDefinitionInDB(
        id=uuid.uuid4(),
        **function_create.model_dump(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    embedding = (await embed([function_create.description]))[0]

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        **function_create.model_dump(),
        newest_update_description="First version",
        definition_id=function_definition_obj.id,
        version=1,
        embedding=embedding,
        implementation_script_id=implementation_script_obj.id,
        setup_script_id=setup_script_obj.id if setup_script_obj else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function_definition).values(**function_definition_obj.model_dump()), commit_after=True)
    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    input_object_group_definition_records = [
        FunctionInputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=input.structure_id,
            name=input.name,
            description=input.description,
            required=input.required,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input in function_create.input_object_groups
    ]

    if input_object_group_definition_records:
        await execute(insert(function_input_object_group_definition).values(input_object_group_definition_records), commit_after=True)

    output_object_group_definition_records = [
        FunctionOutputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=output.structure_id,
            output_entity_id_name=output.output_entity_id_name,
            name=output.name,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_object_group_definitions
    ]

    if output_object_group_definition_records:
        await execute(insert(function_output_object_group_definition).values(output_object_group_definition_records), commit_after=True)

    return Function(**function_obj.model_dump(),
                    definition=function_definition_obj,
                    input_object_groups=[FunctionInputObjectGroupDefinitionInDB(
                        **i) for i in input_object_group_definition_records],
                    output_object_groups=[FunctionOutputObjectGroupDefinitionInDB(
                        **o) for o in output_object_group_definition_records],
                    implementation_script=implementation_script_obj,
                    setup_script=setup_script_obj if setup_script_obj else None)


async def update_function(user_id: uuid.UUID, function_update: FunctionUpdateCreate) -> Function:
    max_version_subquery = select(func.max(function.c.version)).where(
        function.c.definition_id == function_update.definition_id)
    existing_fn = await fetch_one(select(function).where(and_(function.c.definition_id == function_update.definition_id,
                                                              function.c.version == max_version_subquery)))

    if function_update.updated_description:
        embedding = (await embed([function_update.updated_description]))[0]
    else:
        embedding = existing_fn["embedding"]

    implementation_script_obj = await create_script(user_id, function_update.new_implementation_create)
    if function_update.new_setup_create:
        setup_script_obj = await create_script(user_id, function_update.new_setup_create)
    else:
        setup_script_obj = None

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        python_function_name=function_update.updated_python_function_name if function_update.updated_python_function_name else existing_fn[
            "python_function_name"],
        definition_id=function_update.definition_id,
        version=existing_fn["version"] + 1,
        newest_update_description=function_update.updates_made_description,
        docstring=function_update.updated_docstring if function_update.updated_docstring else existing_fn[
            "docstring"],
        description=function_update.updated_description if function_update.updated_description else existing_fn[
            "description"],
        default_args=function_update.updated_default_args if function_update.updated_default_args else existing_fn[
            "default_args"],
        args_schema=function_update.updated_args_schema if function_update.updated_args_schema else existing_fn[
            "args_schema"],
        output_variables_schema=function_update.updated_output_variables_schema if function_update.updated_output_variables_schema else existing_fn[
            "output_variables_schema"],
        embedding=embedding,
        implementation_script_id=implementation_script_obj.id,
        setup_script_id=setup_script_obj.id if setup_script_obj else existing_fn[
            "setup_script_id"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    if function_update.input_object_groups_to_add:
        input_object_group_definition_records = [
            FunctionInputObjectGroupDefinitionInDB(
                id=uuid.uuid4(),
                function_id=function_obj.id,
                structure_id=input.structure_id,
                name=input.name,
                description=input.description,
                required=input.required,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ).model_dump() for input in function_update.input_object_groups_to_add
        ]
        await execute(insert(function_input_object_group_definition).values(input_object_group_definition_records), commit_after=True)

    if function_update.output_object_group_definitions_to_add:
        output_object_group_definition_records = [
            FunctionOutputObjectGroupDefinitionInDB(
                id=uuid.uuid4(),
                function_id=function_obj.id,
                structure_id=output.structure_id,
                output_entity_id_name=output.output_entity_id_name,
                name=output.name,
                description=output.description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ).model_dump() for output in function_update.output_object_group_definitions_to_add
        ]
        await execute(insert(function_output_object_group_definition).values(output_object_group_definition_records), commit_after=True)

    if function_update.input_object_groups_to_remove:
        await execute(delete(function_input_object_group_definition).where(function_input_object_group_definition.c.id.in_(function_update.input_object_groups_to_remove)), commit_after=True)

    if function_update.output_object_group_definitions_to_remove:
        await execute(delete(function_output_object_group_definition).where(function_output_object_group_definition.c.id.in_(function_update.output_object_group_definitions_to_remove)), commit_after=True)

    return (await get_functions([function_obj.id]))[0]


async def get_functions(function_ids: List[uuid.UUID]) -> List[Function]:
    function_query = select(function).where(function.c.id.in_(function_ids))
    functions = await fetch_all(function_query)

    function_definition_query = select(function_definition).where(
        function_definition.c.id.in_([f["definition_id"] for f in functions]))
    function_definition_records = await fetch_all(function_definition_query)

    input_object_group_definition_query = select(function_input_object_group_definition).where(
        function_input_object_group_definition.c.function_id.in_(function_ids))
    input_object_group_definition_records = await fetch_all(input_object_group_definition_query)

    output_object_group_definition_query = select(function_output_object_group_definition).where(
        function_output_object_group_definition.c.function_id.in_(function_ids))
    output_object_group_definition_records = await fetch_all(output_object_group_definition_query)

    implementation_scripts = await get_scripts(
        [f["implementation_script_id"] for f in functions])
    setup_scripts = await get_scripts(
        [f["setup_script_id"] for f in functions if f["setup_script_id"]])

    output_objs = []
    for function_id in function_ids:
        function_record = next(f for f in functions if f["id"] == function_id)
        function_definition_record = next(
            f for f in function_definition_records if f["id"] == function_record["definition_id"])
        input_object_group_definition_records = [
            i for i in input_object_group_definition_records if i["function_id"] == function_id]
        output_object_group_definition_records = [
            o for o in output_object_group_definition_records if o["function_id"] == function_id]
        implementation_script = next(
            s for s in implementation_scripts if s.id == function_record["implementation_script_id"])
        setup_script = next((
            s for s in setup_scripts if s.id == function_record["setup_script_id"]), None)

        description = get_function_description(
            FunctionWithoutEmbedding(**function_record),
            FunctionDefinitionInDB(**function_definition_record),
            [FunctionInputObjectGroupDefinitionInDB(
                **i) for i in input_object_group_definition_records],
            [FunctionOutputObjectGroupDefinitionInDB(
                **o) for o in output_object_group_definition_records],
            implementation_script)

        output_objs.append(
            Function(**function_record,
                     definition=function_definition_record,
                     input_object_groups=input_object_group_definition_records,
                     output_object_groups=output_object_group_definition_records,
                     implementation_script=implementation_script,
                     setup_script=setup_script,
                     description_for_agent=description))

    return output_objs
