import uuid
from datetime import datetime, timezone
from sqlalchemy import insert

from synesis_api.database.service import execute
from synesis_api.modules.function.models import function, function_input_structure, function_output_structure, function_output_variable
from synesis_schemas.main_server import FunctionInDB, FunctionCreate, FunctionInputStructureInDB, FunctionOutputStructureInDB, FunctionOutputVariableInDB
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
        config_dict=function_create.default_args,
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
