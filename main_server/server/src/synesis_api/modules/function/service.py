import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy import insert, select, func
from sqlalchemy import and_

from synesis_api.database.service import execute, fetch_all, fetch_one
from synesis_api.modules.function.models import (
    function,
    function_definition
)
from synesis_schemas.main_server import (
    FunctionInDB,
    FunctionCreate,
    FunctionDefinitionInDB,
    FunctionUpdateCreate,
    Function,
    FunctionWithoutEmbedding,
)
from synesis_api.utils.rag_utils import embed
from synesis_api.modules.function.description import get_function_description


async def create_function(user_id: uuid.UUID, function_create: FunctionCreate) -> Function:

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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function_definition).values(**function_definition_obj.model_dump()), commit_after=True)
    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    description = get_function_description(
        FunctionWithoutEmbedding(**function_obj.model_dump()),
        function_definition_obj,
        function_obj.implementation_script_path
    )

    return Function(**function_obj.model_dump(),
                    definition=function_definition_obj,
                    description_for_agent=description)


async def update_function(user_id: uuid.UUID, function_update: FunctionUpdateCreate) -> Function:
    max_version_subquery = select(func.max(function.c.version)).where(
        function.c.definition_id == function_update.definition_id)
    existing_fn = await fetch_one(select(function).where(and_(function.c.definition_id == function_update.definition_id,
                                                              function.c.version == max_version_subquery)))

    if function_update.updated_description:
        embedding = (await embed([function_update.updated_description]))[0]
    else:
        embedding = existing_fn["embedding"]

    implementation_script_path = function_update.new_implementation_script_path
    setup_script_path = function_update.new_setup_script_path if function_update.new_setup_script_path else existing_fn.get(
        "setup_script_path")

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
        implementation_script_path=implementation_script_path,
        setup_script_path=setup_script_path,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    return (await get_functions([function_obj.id]))[0]


async def get_functions(function_ids: List[uuid.UUID]) -> List[Function]:
    function_query = select(function).where(function.c.id.in_(function_ids))
    functions = await fetch_all(function_query)

    function_definition_query = select(function_definition).where(
        function_definition.c.id.in_([f["definition_id"] for f in functions]))
    function_definition_records = await fetch_all(function_definition_query)

    output_objs = []
    for function_id in function_ids:
        function_record = next(f for f in functions if f["id"] == function_id)
        function_definition_record = next(
            f for f in function_definition_records if f["id"] == function_record["definition_id"])

        description = get_function_description(
            FunctionWithoutEmbedding(**function_record),
            FunctionDefinitionInDB(**function_definition_record),
            function_record["implementation_script_path"])

        output_objs.append(
            Function(**function_record,
                     definition=function_definition_record,
                     description_for_agent=description))

    return output_objs
