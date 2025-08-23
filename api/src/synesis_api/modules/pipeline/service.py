import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, insert, or_

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.pipeline.models import (
    model, modality, source, programming_language_version,
    programming_language, task, model_task, function, function_input, function_output, pipeline, function_in_pipeline
)
from synesis_api.modules.pipeline.schema import (
    PipelineInDB,
    ModalityInDB,
    SourceInDB,
    ProgrammingLanguageVersionInDB,
    TaskInDB,
    ProgrammingLanguageInDB,
    ModelInDB,
    ModelTaskInDB,
    FunctionInDB,
    FunctionInputInDB,
    FunctionOutputInDB,
    FunctionInputCreate,
    FunctionOutputCreate,
    FunctionInPipelineInDB,
    FunctionWithoutEmbedding
)
from synesis_api.utils.rag_utils import embed


async def create_pipeline(
    name: str,
    description: str,
    user_id: uuid.UUID,
    function_ids: List[uuid.UUID]
) -> PipelineInDB:

    pipeline_obj = PipelineInDB(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        description=description,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(pipeline).values(**pipeline_obj.model_dump()), commit_after=True)

    fn_in_pipeline_records = []
    for i, function_id in enumerate(function_ids):
        next_function_id = function_ids[i +
                                        1] if i+1 < len(function_ids) else None
        function_in_pipeline_obj = FunctionInPipelineInDB(
            id=uuid.uuid4(),
            pipeline_id=pipeline_obj.id,
            function_id=function_id,
            next_function_id=next_function_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        fn_in_pipeline_records.append(function_in_pipeline_obj.model_dump())

    await execute(insert(function_in_pipeline).values(fn_in_pipeline_records), commit_after=True)

    return pipeline_obj


async def get_user_pipelines(user_id: uuid.UUID) -> List[PipelineInDB]:
    pipelines = await fetch_all(
        select(pipeline).where(pipeline.c.user_id == user_id)
    )
    pipeline_objs = [PipelineInDB(**p) for p in pipelines]
    return pipeline_objs


async def create_function(
    name: str,
    description: str,
    implementation_script_path: str,
    setup_script_path: str,
    inputs: List[FunctionInputCreate],
    outputs: List[FunctionOutputCreate],
    function_id: Optional[uuid.UUID] = None
) -> FunctionInDB:

    if function_id is None:
        function_id = uuid.uuid4()

    embedding = (await embed([description]))[0]

    function_obj = FunctionInDB(
        id=function_id,
        name=name,
        description=description,
        implementation_script_path=implementation_script_path,
        setup_script_path=setup_script_path,
        embedding=embedding,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(insert(function).values(**function_obj.model_dump()), commit_after=True)

    input_records = [
        FunctionInputInDB(
            id=uuid.uuid4(),
            function_id=function_id,
            structure_id=input.structure_id,
            name=input.name,
            description=input.description,
            required=input.required,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for input in inputs
    ]

    await execute(insert(function_input).values(input_records), commit_after=True)

    output_records = [
        FunctionOutputInDB(
            id=uuid.uuid4(),
            function_id=function_id,
            structure_id=output.structure_id,
            name=output.name,
            description=output.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ).model_dump() for output in outputs
    ]

    await execute(insert(function_output).values(output_records), commit_after=True)

    return function_obj


async def _get_or_create_modalities(names: List[str], descriptions: Optional[List[str]] = None) -> List[ModalityInDB]:
    """Get existing modalities or create new ones"""

    assert descriptions is None or len(names) == len(
        descriptions), "Names and descriptions must have the same length"

    modalities = []
    existing_modalities = await fetch_all(
        select(modality).where(modality.c.name.in_(names))
    )

    # Create a map of existing modalities by name
    existing_by_name = {m["name"]: m for m in existing_modalities}

    for i, name in enumerate(names):
        description = descriptions[i] if descriptions else None

        if name in existing_by_name:
            modalities.append(ModalityInDB(**existing_by_name[name]))
        else:
            modality_id = uuid.uuid4()

            modality_obj = ModalityInDB(
                id=modality_id,
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            await execute(insert(modality).values(**modality_obj.model_dump()), commit_after=True)
            modalities.append(modality_obj)

    return modalities


async def _get_or_create_tasks(names: List[str], descriptions: Optional[List[str]] = None) -> List[TaskInDB]:
    """Get existing tasks or create new ones"""

    assert descriptions is None or len(names) == len(
        descriptions), "Names and descriptions must have the same length"

    tasks = []
    existing_tasks = await fetch_all(
        select(task).where(task.c.name.in_(names))
    )

    # Create a map of existing tasks by name
    existing_by_name = {t["name"]: t for t in existing_tasks}

    for i, name in enumerate(names):
        description = descriptions[i] if descriptions else None

        if name in existing_by_name:
            tasks.append(TaskInDB(**existing_by_name[name]))
        else:
            task_obj = TaskInDB(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(task).values(**task_obj.model_dump()), commit_after=True)
            tasks.append(task_obj)

    return tasks


async def _get_or_create_sources(names: List[str], descriptions: Optional[List[str]] = None) -> List[SourceInDB]:
    """Get existing sources or create new ones"""

    assert descriptions is None or len(names) == len(
        descriptions), "Names and descriptions must have the same length"

    sources = []
    existing_sources = await fetch_all(
        select(source).where(source.c.name.in_(names))
    )

    # Create a map of existing sources by name
    existing_by_name = {s["name"]: s for s in existing_sources}

    for i, name in enumerate(names):
        description = descriptions[i] if descriptions else None

        if name in existing_by_name:
            sources.append(SourceInDB(**existing_by_name[name]))
        else:
            source_obj = SourceInDB(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await execute(insert(source).values(**source_obj.model_dump()), commit_after=True)
            sources.append(source_obj)

    return sources


async def _get_or_create_programming_languages(names: List[str], descriptions: Optional[List[str]] = None) -> List[ProgrammingLanguageInDB]:
    """Get existing programming languages or create new ones"""

    assert descriptions is None or len(names) == len(
        descriptions), "Names and descriptions must have the same length"

    programming_languages = []
    existing_programming_languages = await fetch_all(
        select(programming_language).where(
            programming_language.c.name.in_(names))
    )

    # Create a map of existing programming languages by name
    existing_by_name = {
        pl["name"]: pl for pl in existing_programming_languages}

    for i, name in enumerate(names):
        description = descriptions[i] if descriptions else None

        if name in existing_by_name:
            programming_languages.append(
                ProgrammingLanguageInDB(**existing_by_name[name]))
        else:
            programming_language_obj = ProgrammingLanguageInDB(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await execute(insert(programming_language).values(**programming_language_obj.model_dump()), commit_after=True)
            programming_languages.append(programming_language_obj)

    return programming_languages


async def _get_or_create_programming_language_versions(
    programming_language_ids: List[uuid.UUID],
    versions: List[str]
) -> List[ProgrammingLanguageVersionInDB]:
    """Get existing programming language versions or create new ones"""

    assert len(programming_language_ids) == len(
        versions), "Programming language IDs and versions must have the same length"

    programming_language_versions = []

    # Build query to find existing versions
    conditions = []
    for pl_id, version in zip(programming_language_ids, versions):
        conditions.append(
            (programming_language_version.c.programming_language_id == pl_id) &
            (programming_language_version.c.version == version)
        )

    existing_versions = await fetch_all(
        select(programming_language_version).where(or_(*conditions))
    )

    # Create a map of existing versions by (programming_language_id, version)
    existing_by_key = {(v["programming_language_id"],
                        v["version"]): v for v in existing_versions}

    for programming_language_id, version in zip(programming_language_ids, versions):
        key = (programming_language_id, version)

        if key in existing_by_key:
            programming_language_versions.append(
                ProgrammingLanguageVersionInDB(**existing_by_key[key]))
        else:

            programming_language_version_obj = ProgrammingLanguageVersionInDB(
                id=uuid.uuid4(),
                programming_language_id=programming_language_id,
                version=version,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await execute(
                insert(programming_language_version).values(
                    **programming_language_version_obj.model_dump()),
                commit_after=True
            )
            programming_language_versions.append(
                programming_language_version_obj)

    return programming_language_versions


# TODO: Update to deal with function inputs and outputs
async def create_model(
    name: str,
    description: str,
    owner_id: uuid.UUID,
    public: bool,
    modality_name: str,
    source_name: str,
    programming_language_name: str,
    programming_language_version_name: str,
    setup_script_path: str,
    config_script_path: str,
    input_description: str,
    output_description: str,
    config_parameters: List[str],
    tasks: List[str],
    inference_script_paths: List[str],
    training_script_paths: List[str],
    model_id: Optional[uuid.UUID] = None
) -> ModelInDB:

    # Get IDs from names using the list-based functions
    modalities = await _get_or_create_modalities([modality_name])
    modality = modalities[0]

    sources = await _get_or_create_sources([source_name])
    source = sources[0]

    programming_languages = await _get_or_create_programming_languages(
        [programming_language_name])
    programming_language = programming_languages[0]

    # Get or create programming language version
    programming_language_versions = await _get_or_create_programming_language_versions(
        [programming_language.id],
        [programming_language_version_name]
    )
    programming_language_version = programming_language_versions[0]

    # Get or create tasks
    task_objects = await _get_or_create_tasks(tasks)

    # Insert the model
    if model_id is None:
        model_id = uuid.uuid4()

    model_obj = ModelInDB(
        id=model_id,
        name=name,
        description=description,
        owner_id=owner_id,
        public=public,
        modality_id=modality.id,
        source_id=source.id,
        programming_language_version_id=programming_language_version.id,
        setup_script_path=setup_script_path,
        config_script_path=config_script_path,
        input_description=input_description,
        output_description=output_description,
        config_parameters=config_parameters,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    await execute(
        insert(model).values(**model_obj.model_dump()),
        commit_after=True
    )

    # Insert model_task relationships
    for i, task_object in enumerate(task_objects):

        inference_fn_desc = f"Inference function for model {name} and task {task_object.name}"
        training_fn_desc = f"Training function for model {name} and task {task_object.name}"

        embeddings = await embed([inference_fn_desc, training_fn_desc])

        inference_function_obj = FunctionInDB(
            id=uuid.uuid4(),
            name=f"{name}_{task_object.id}",
            script_path=inference_script_paths[i],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            description=inference_fn_desc,
            embedding=embeddings[0]
        )

        training_function_obj = FunctionInDB(
            id=uuid.uuid4(),
            name=f"{name}_{task_object.id}",
            script_path=training_script_paths[i],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            description=training_fn_desc,
            embedding=embeddings[1]
        )

        await execute(
            insert(function).values(
                [inference_function_obj.model_dump(), training_function_obj.model_dump()]),
            commit_after=True
        )

        model_task_obj = ModelTaskInDB(
            model_id=model_id,
            task_id=task_object.id,
            inference_script_path=inference_script_paths[i],
            training_script_path=training_script_paths[i],
            inference_function_id=inference_function_obj.id,
            training_function_id=training_function_obj.id
        )

        await execute(
            insert(model_task).values(**model_task_obj.model_dump()),
            commit_after=True
        )

    return model_obj


async def search_functions(search_query: str, k: int = 10) -> List[FunctionWithoutEmbedding]:

    query_vector = (await embed([search_query]))[0]

    function_query = select(
        function
    ).order_by(
        function.c.embedding.cosine_distance(query_vector)
    ).limit(k)

    fns = await fetch_all(function_query)

    function_ids = [fn["id"] for fn in fns]

    function_input_structures_query = select(
        function_input
    ).where(function_input.c.function_id.in_(function_ids))

    function_output_structures_query = select(
        function_output
    ).where(function_output.c.function_id.in_(function_ids))

    fn_inputs = await fetch_all(function_input_structures_query)
    fn_outputs = await fetch_all(function_output_structures_query)

    return [FunctionWithoutEmbedding(**f, inputs=fn_inputs, outputs=fn_outputs) for f in fns]


async def check_function_ids_exist(function_ids: List[uuid.UUID]) -> bool:
    """Check if all function IDs exist"""

    query = select(function.c.id).where(function.c.id.in_(function_ids))
    results = await fetch_all(query)

    return len(results) == len(function_ids)
