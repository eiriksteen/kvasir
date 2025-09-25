import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import insert, select

from synesis_api.database.service import execute, fetch_all
from synesis_api.modules.function.models import function, function_input_structure, function_output_structure, function_output_variable
from synesis_schemas.main_server import FunctionInDB, FunctionCreate, FunctionInputStructureInDB, FunctionOutputStructureInDB, FunctionOutputVariableInDB, FunctionBare
from synesis_api.utils.rag_utils import embed


async def create_function(function_create: FunctionCreate) -> FunctionInDB:

    embedding = (await embed([function_create.description]))[0]

    function_obj = FunctionInDB(
        id=uuid.uuid4(),
        name=function_create.name,
        description=function_create.description,
        type=function_create.type,
        implementation_script_path=str(
            function_create.implementation_script_path),
        setup_script_path=str(
            function_create.setup_script_path) if function_create.setup_script_path else None,
        default_args=function_create.default_args,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    input_structure_records = [
        FunctionInputStructureInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=input.structure_id,
            name=input.name,
            description=input.description,
            required=input.required,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input in function_create.input_structures
    ]

    if input_structure_records:
        await execute(insert(function_input_structure).values(input_structure_records), commit_after=True)

    output_structure_records = [
        FunctionOutputStructureInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            structure_id=output.structure_id,
            name=output.name,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_structures
    ]

    if output_structure_records:
        await execute(insert(function_output_structure).values(output_structure_records), commit_after=True)

    output_variable_records = [
        FunctionOutputVariableInDB(
            id=uuid.uuid4(),
            function_id=function_obj.id,
            name=output.name,
            python_type=output.python_type,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in function_create.output_variables
    ]

    if output_variable_records:
        await execute(insert(function_output_variable).values(output_variable_records), commit_after=True)

    return function_obj


async def get_functions(function_ids: List[uuid.UUID]) -> List[FunctionBare]:

    function_query = select(function).where(function.c.id.in_(function_ids))
    functions = await fetch_all(function_query)

    input_structure_query = select(function_input_structure).where(
        function_input_structure.c.function_id.in_(function_ids))
    input_structures = await fetch_all(input_structure_query)

    output_structure_query = select(function_output_structure).where(
        function_output_structure.c.function_id.in_(function_ids))
    output_structures = await fetch_all(output_structure_query)

    output_variable_query = select(function_output_variable).where(
        function_output_variable.c.function_id.in_(function_ids))
    output_variables = await fetch_all(output_variable_query)

    output_objs = []
    for function_id in function_ids:
        function_record = next(f for f in functions if f["id"] == function_id)
        input_structures_records = [
            i for i in input_structures if i["function_id"] == function_id]
        output_structures_records = [
            o for o in output_structures if o["function_id"] == function_id]
        output_variables_records = [
            v for v in output_variables if v["function_id"] == function_id]
        output_objs.append(
            FunctionBare(**function_record,
                         input_structures=input_structures_records,
                         output_structures=output_structures_records,
                         output_variables=output_variables_records)
        )

    return output_objs
