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
    function_output_object_group_definition,
    function_output_variable_definition
)
from synesis_schemas.main_server import (
    FunctionInDB,
    FunctionCreate,
    FunctionInputObjectGroupDefinitionInDB,
    FunctionOutputObjectGroupDefinitionInDB,
    FunctionOutputVariableDefinitionInDB,
    FunctionBare,
    FunctionDefinitionInDB,
    FunctionUpdateCreate
)
from synesis_api.utils.rag_utils import embed


async def create_function(function_create: FunctionCreate) -> FunctionInDB:

    function_definition_obj = FunctionDefinitionInDB(
        id=uuid.uuid4(),
        name=function_create.name,
        type=function_create.type,
        args_dataclass_name=function_create.args_dataclass_name,
        input_dataclass_name=function_create.input_dataclass_name,
        output_dataclass_name=function_create.output_dataclass_name,
        output_variables_dataclass_name=function_create.output_variables_dataclass_name,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    embedding = (await embed([function_create.description]))[0]

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        description=function_create.description,
        definition_id=function_definition_obj.id,
        version=1,
        implementation_script_path=str(
            function_create.implementation_script_path),
        setup_script_path=str(
            function_create.setup_script_path) if function_create.setup_script_path else None,
        default_args_dict=function_create.default_args_dict,
        embedding=embedding,
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
        ).model_dump() for input in function_create.input_object_group_descriptions
    ]

    if input_object_group_definition_records:
        await execute(insert(function_input_object_group_definition).values(input_object_group_definition_records), commit_after=True)

    output_object_group_definition_records = [
        FunctionOutputObjectGroupDefinitionInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=output.structure_id,
            name=output.name,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_object_group_descriptions
    ]

    if output_object_group_definition_records:
        await execute(insert(function_output_object_group_definition).values(output_object_group_definition_records), commit_after=True)

    output_variable_definition_records = [
        FunctionOutputVariableDefinitionInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            name=output.name,
            python_type=output.python_type,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_variables_descriptions
    ]

    if output_variable_definition_records:
        await execute(insert(function_output_variable_definition).values(output_variable_definition_records), commit_after=True)

    return FunctionBare(**function_obj.model_dump(),
                        name=function_definition_obj.name,
                        type=function_definition_obj.type,
                        args_dataclass_name=function_definition_obj.args_dataclass_name,
                        input_dataclass_name=function_definition_obj.input_dataclass_name,
                        output_dataclass_name=function_definition_obj.output_dataclass_name,
                        output_variables_dataclass_name=function_definition_obj.output_variables_dataclass_name,
                        input_object_groups=input_object_group_definition_records,
                        output_object_groups=output_object_group_definition_records,
                        output_variables=output_variable_definition_records)


async def update_function(function_update: FunctionUpdateCreate) -> FunctionInDB:
    max_version_subquery = select(func.max(function.c.version)).where(
        function.c.definition_id == function_update.definition_id)
    existing_fn = await fetch_one(select(function).where(and_(function.c.definition_id == function_update.definition_id,
                                                              function.c.version == max_version_subquery)))

    if function_update.updated_description:
        embedding = (await embed([function_update.updated_description]))[0]
    else:
        embedding = existing_fn["embedding"]

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        definition_id=function_update.definition_id,
        version=existing_fn["version"] + 1,
        implementation_script_path=function_update.updated_implementation_script_path if function_update.updated_implementation_script_path else existing_fn[
            "implementation_script_path"],
        description=function_update.updated_description if function_update.updated_description else existing_fn[
            "description"],
        setup_script_path=function_update.updated_setup_script_path if function_update.updated_setup_script_path else existing_fn[
            "setup_script_path"],
        default_args_dict=function_update.updated_default_args_dict if function_update.updated_default_args_dict else existing_fn[
            "default_args_dict"],
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    if function_update.input_object_group_descriptions_to_add:
        input_object_group_definition_records = [
            FunctionInputObjectGroupDefinitionInDB(
                id=uuid.uuid4(),
                function_id=function_obj.id,
                structure_id=input.structure_id,
                name=input.name,
                description=input.description,
                required=input.required,
            ).model_dump() for input in function_update.input_object_group_descriptions_to_add
        ]
        await execute(insert(function_input_object_group_definition).values(input_object_group_definition_records), commit_after=True)

    if function_update.output_object_group_descriptions_to_add:
        output_object_group_definition_records = [
            FunctionOutputObjectGroupDefinitionInDB(
                id=uuid.uuid4(),
                function_id=function_obj.id,
                structure_id=output.structure_id,
                name=output.name,
                description=output.description,
            ).model_dump() for output in function_update.output_object_group_descriptions_to_add
        ]
        await execute(insert(function_output_object_group_definition).values(output_object_group_definition_records), commit_after=True)

    if function_update.output_variables_descriptions_to_add:
        output_variable_definition_records = [
            FunctionOutputVariableDefinitionInDB(
                id=uuid.uuid4(),
                function_id=function_obj.id,
                name=output.name,
                python_type=output.python_type,
                description=output.description,
            ).model_dump() for output in function_update.output_variables_descriptions_to_add
        ]
        await execute(insert(function_output_variable_definition).values(output_variable_definition_records), commit_after=True)

    if function_update.input_object_group_descriptions_to_remove:
        await execute(delete(function_input_object_group_definition).where(function_input_object_group_definition.c.id.in_(function_update.input_object_group_descriptions_to_remove)), commit_after=True)

    if function_update.output_object_group_descriptions_to_remove:
        await execute(delete(function_output_object_group_definition).where(function_output_object_group_definition.c.id.in_(function_update.output_object_group_descriptions_to_remove)), commit_after=True)

    if function_update.output_variables_descriptions_to_remove:
        await execute(delete(function_output_variable_definition).where(function_output_variable_definition.c.id.in_(function_update.output_variables_descriptions_to_remove)), commit_after=True)

    return function_obj


async def get_functions(function_ids: List[uuid.UUID]) -> List[FunctionBare]:

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

    output_variable_definition_query = select(function_output_variable_definition).where(
        function_output_variable_definition.c.function_id.in_(function_ids))
    output_variable_definition_records = await fetch_all(output_variable_definition_query)

    output_objs = []
    for function_id in function_ids:
        function_record = next(f for f in functions if f["id"] == function_id)
        function_definition_record = next(
            f for f in function_definition_records if f["id"] == function_record["definition_id"])
        input_object_group_definition_records = [
            i for i in input_object_group_definition_records if i["function_id"] == function_id]
        output_object_group_definition_records = [
            o for o in output_object_group_definition_records if o["function_id"] == function_id]
        output_variable_definition_records = [
            v for v in output_variable_definition_records if v["function_id"] == function_id]
        output_objs.append(
            FunctionBare(**function_record,
                         name=function_definition_record["name"],
                         type=function_definition_record["type"],
                         args_dataclass_name=function_definition_record["args_dataclass_name"],
                         input_dataclass_name=function_definition_record["input_dataclass_name"],
                         output_dataclass_name=function_definition_record["output_dataclass_name"],
                         output_variables_dataclass_name=function_definition_record[
                             "output_variables_dataclass_name"],
                         input_object_groups=input_object_group_definition_records,
                         output_object_groups=output_object_group_definition_records,
                         output_variables=output_variable_definition_records)
        )

    return output_objs
