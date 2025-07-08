import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, join, insert, or_
from synesis_api.database.service import fetch_all, fetch_one, execute
from synesis_api.modules.automation.models import (
    model, modality, source, programming_language_version,
    programming_language, task, model_task
)
from synesis_api.modules.automation.schema import ModelJoined, Modality, Source, ProgrammingLanguageVersion, Task, ProgrammingLanguage
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.modules.jobs.models import jobs
from synesis_api.modules.model_integration.models import model_integration_jobs_results


async def get_or_create_modalities(names: List[str], descriptions: Optional[List[str]] = None) -> List[Modality]:
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
            modalities.append(Modality(**existing_by_name[name]))
        else:
            modality_id = uuid.uuid4()

            modality_obj = Modality(
                id=modality_id,
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )

            await execute(insert(modality).values(**modality_obj.model_dump()), commit_after=True)
            modalities.append(modality_obj)

    return modalities


async def get_or_create_tasks(names: List[str], descriptions: Optional[List[str]] = None) -> List[Task]:
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
            tasks.append(Task(**existing_by_name[name]))
        else:
            task_obj = Task(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(task).values(**task_obj.model_dump()), commit_after=True)
            tasks.append(task_obj)

    return tasks


async def get_or_create_sources(names: List[str], descriptions: Optional[List[str]] = None) -> List[Source]:
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
            sources.append(Source(**existing_by_name[name]))
        else:
            source_obj = Source(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(source).values(**source_obj.model_dump()), commit_after=True)
            sources.append(source_obj)

    return sources


async def get_or_create_programming_languages(names: List[str], descriptions: Optional[List[str]] = None) -> List[ProgrammingLanguage]:
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
                ProgrammingLanguage(**existing_by_name[name]))
        else:
            programming_language_obj = ProgrammingLanguage(
                id=uuid.uuid4(),
                name=name,
                description=description,
                created_at=datetime.now(timezone.utc)
            )
            await execute(insert(programming_language).values(**programming_language_obj.model_dump()), commit_after=True)
            programming_languages.append(programming_language_obj)

    return programming_languages


async def get_or_create_programming_language_versions(
    programming_language_ids: List[uuid.UUID],
    versions: List[str]
) -> List[ProgrammingLanguageVersion]:
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
                ProgrammingLanguageVersion(**existing_by_key[key]))
        else:

            programming_language_version_obj = ProgrammingLanguageVersion(
                id=uuid.uuid4(),
                programming_language_id=programming_language_id,
                version=version,
                created_at=datetime.now(timezone.utc)
            )
            await execute(
                insert(programming_language_version).values(
                    **programming_language_version_obj.model_dump()),
                commit_after=True
            )
            programming_language_versions.append(
                programming_language_version_obj)

    return programming_language_versions


async def insert_model(
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
) -> ModelJoined:
    """
    Insert a new model with all related entities.

    Args:
        name: Model name
        description: Model description
        owner_id: ID of the user who owns this model
        modality: Name of the modality
        source: Name of the source
        programming_language: Name of the programming language
        programming_language_version: Version string (e.g., "3.8", "3.9")
        setup_script_path: Path to setup script
        config_script_path: Path to config script
        input_description: Description of model inputs
        output_description: Description of model outputs
        config_parameters: List of configuration parameter names
        task_ids: List of task IDs this model supports
        inference_script_paths: Dict mapping task_id to inference script path
        training_script_paths: Dict mapping task_id to training script path
    """

    # Get IDs from names using the list-based functions
    modalities = await get_or_create_modalities([modality_name])
    modality = modalities[0]

    sources = await get_or_create_sources([source_name])
    source = sources[0]

    programming_languages = await get_or_create_programming_languages([programming_language_name])
    programming_language = programming_languages[0]

    # Get or create programming language version
    programming_language_versions = await get_or_create_programming_language_versions(
        [programming_language.id],
        [programming_language_version_name]
    )
    programming_language_version = programming_language_versions[0]

    # Get or create tasks
    task_objects = await get_or_create_tasks(tasks)
    task_ids = [task.id for task in task_objects]

    # Insert the model
    if model_id is None:
        model_id = uuid.uuid4()

    await execute(
        insert(model).values(
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
            config_parameters=config_parameters
        ),
        commit_after=True
    )

    # Insert model_task relationships
    for i, task_id in enumerate(task_ids):

        await execute(
            insert(model_task).values(
                model_id=model_id,
                task_id=task_id,
                inference_script_path=inference_script_paths[i],
                training_script_path=training_script_paths[i]
            ),
            commit_after=True
        )

    # Return the complete ModelJoined object
    return await get_model_joined(model_id)


async def model_is_public(model_id: uuid.UUID) -> bool:
    """Check if a model is public"""
    model_record = await fetch_one(
        select(model).where(model.c.id == model_id, model.c.public == True)
    )
    return model_record is not None


async def user_owns_model(user_id: uuid.UUID, model_id: uuid.UUID) -> bool:
    """Check if a user owns a specific model"""
    model_record = await fetch_one(
        select(model).where(
            model.c.id == model_id,
            model.c.owner_id == user_id
        )
    )
    return model_record is not None


async def get_integration_jobs_for_user_models(user_id: uuid.UUID) -> dict[uuid.UUID, List[dict]]:
    """
    Get all integration jobs for models owned by a user.

    Args:
        user_id: The ID of the user

    Returns:
        A dictionary mapping model_id to a list of job metadata dictionaries
    """
    query = select(
        model_integration_jobs_results.c.model_id,
        jobs.c.id,
        jobs.c.type,
        jobs.c.status,
        jobs.c.job_name,
        jobs.c.started_at,
        jobs.c.completed_at
    ).join(
        jobs, jobs.c.id == model_integration_jobs_results.c.job_id
    ).join(
        model, model.c.id == model_integration_jobs_results.c.model_id
    ).where(
        model.c.owner_id == user_id
    )

    results = await fetch_all(query)

    # Group jobs by model_id
    jobs_by_model = {}
    for row in results:
        model_id = row["model_id"]
        if model_id not in jobs_by_model:
            jobs_by_model[model_id] = []

        jobs_by_model[model_id].append({
            "id": row["id"],
            "type": row["type"],
            "status": row["status"],
            "job_name": row["job_name"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"]
        })

    return jobs_by_model


async def get_user_models(user_id: uuid.UUID, include_integration_jobs: bool = False) -> List[ModelJoined]:
    """Get all models owned by a specific user"""

    # Join all the necessary tables and filter by owner
    query = (
        select(
            model,
            modality.c.name.label("modality_name"),
            modality.c.description.label("modality_description"),
            source.c.name.label("source_name"),
            source.c.description.label("source_description"),
            source.c.created_at.label("source_created_at"),
            programming_language_version.c.id.label("pl_version_id"),
            programming_language_version.c.programming_language_id.label(
                "pl_id"),
            programming_language_version.c.version.label("pl_version"),
            programming_language_version.c.created_at.label(
                "pl_version_created_at"),
            programming_language.c.name.label("pl_name"),
            programming_language.c.description.label("pl_description"),
            programming_language.c.created_at.label("pl_created_at")
        )
        .select_from(
            model.join(modality, model.c.modality_id == modality.c.id)
                 .join(source, model.c.source_id == source.c.id)
                 .join(programming_language_version, model.c.programming_language_version_id == programming_language_version.c.id)
                 .join(programming_language, programming_language_version.c.programming_language_id == programming_language.c.id)
        )
        .where(model.c.owner_id == user_id)
    )

    results = await fetch_all(query)

    models_joined = []
    for result in results:
        # Get tasks for this model
        tasks_query = (
            select(task)
            .select_from(
                model_task.join(task, model_task.c.task_id == task.c.id)
            )
            .where(model_task.c.model_id == result["id"])
        )

        tasks_result = await fetch_all(tasks_query)
        tasks = [Task(**task) for task in tasks_result]

        # Construct the joined model
        modality_obj = Modality(
            id=result["modality_id"],
            name=result["modality_name"],
            description=result["modality_description"]
        )

        source_obj = Source(
            id=result["source_id"],
            name=result["source_name"],
            description=result["source_description"],
            created_at=result["source_created_at"]
        )

        programming_language_version_obj = ProgrammingLanguageVersion(
            id=result["pl_version_id"],
            programming_language_id=result["pl_id"],
            version=result["pl_version"],
            created_at=result["pl_version_created_at"]
        )

        model_joined = ModelJoined(
            **result,
            modality=modality_obj,
            source=source_obj,
            programming_language_version=programming_language_version_obj,
            tasks=tasks
        )

        models_joined.append(model_joined)

    if include_integration_jobs:
        # Get integration jobs for all user models
        integration_jobs_by_model = await get_integration_jobs_for_user_models(user_id)

        # Populate integration_jobs for each model
        for model_joined in models_joined:
            model_jobs = integration_jobs_by_model.get(model_joined.id, [])
            model_joined.integration_jobs = [
                JobMetadata(**job) for job in model_jobs]

    return models_joined


async def get_model_joined(model_id: uuid.UUID, include_integration_jobs: bool = False) -> ModelJoined:
    """Get a single ModelJoined by model_id"""

    # Join all the necessary tables
    query = (
        select(
            model,
            modality.c.name.label("modality_name"),
            modality.c.description.label("modality_description"),
            source.c.name.label("source_name"),
            source.c.description.label("source_description"),
            source.c.created_at.label("source_created_at"),
            programming_language_version.c.id.label("pl_version_id"),
            programming_language_version.c.programming_language_id.label(
                "pl_id"),
            programming_language_version.c.version.label("pl_version"),
            programming_language_version.c.created_at.label(
                "pl_version_created_at"),
            programming_language.c.name.label("pl_name"),
            programming_language.c.description.label("pl_description"),
            programming_language.c.created_at.label("pl_created_at")
        )
        .select_from(
            model.join(modality, model.c.modality_id == modality.c.id)
                 .join(source, model.c.source_id == source.c.id)
                 .join(programming_language_version, model.c.programming_language_version_id == programming_language_version.c.id)
                 .join(programming_language, programming_language_version.c.programming_language_id == programming_language.c.id)
        )
        .where(model.c.id == model_id)
    )

    result = await fetch_one(query)

    if not result:
        raise ValueError(f"Model with id {model_id} not found")

    # Get tasks for this model
    tasks_query = (
        select(task)
        .select_from(
            model_task.join(task, model_task.c.task_id == task.c.id)
        )
        .where(model_task.c.model_id == model_id)
    )

    tasks_result = await fetch_all(tasks_query)
    tasks = [Task(**task) for task in tasks_result]

    # Construct the joined model
    modality_obj = Modality(
        id=result["modality_id"],
        name=result["modality_name"],
        description=result["modality_description"]
    )

    source_obj = Source(
        id=result["source_id"],
        name=result["source_name"],
        description=result["source_description"],
        created_at=result["source_created_at"]
    )

    programming_language_version_obj = ProgrammingLanguageVersion(
        id=result["pl_version_id"],
        programming_language_id=result["pl_id"],
        version=result["pl_version"],
        created_at=result["pl_version_created_at"]
    )

    model_joined = ModelJoined(
        **result,
        modality=modality_obj,
        source=source_obj,
        programming_language_version=programming_language_version_obj,
        tasks=tasks
    )

    if include_integration_jobs:
        # Get integration jobs for this specific model
        integration_jobs_by_model = await get_integration_jobs_for_user_models(result["owner_id"])
        model_jobs = integration_jobs_by_model.get(model_id, [])
        model_joined.integration_jobs = [
            JobMetadata(**job) for job in model_jobs]

    return model_joined


async def get_all_models_public_or_owned(user_id: uuid.UUID, include_integration_jobs: bool = False) -> List[ModelJoined]:
    """Get all ModelJoined objects"""

    # Join all the necessary tables
    query = (
        select(
            model,
            modality.c.name.label("modality_name"),
            modality.c.description.label("modality_description"),
            source.c.name.label("source_name"),
            source.c.description.label("source_description"),
            source.c.created_at.label("source_created_at"),
            programming_language_version.c.id.label("pl_version_id"),
            programming_language_version.c.programming_language_id.label(
                "pl_id"),
            programming_language_version.c.version.label("pl_version"),
            programming_language_version.c.created_at.label(
                "pl_version_created_at"),
            programming_language.c.name.label("pl_name"),
            programming_language.c.description.label("pl_description"),
            programming_language.c.created_at.label("pl_created_at")
        )
        .select_from(
            model.join(modality, model.c.modality_id == modality.c.id)
                 .join(source, model.c.source_id == source.c.id)
                 .join(programming_language_version, model.c.programming_language_version_id == programming_language_version.c.id)
                 .join(programming_language, programming_language_version.c.programming_language_id == programming_language.c.id)
        )
        .where(
            or_(
                model.c.public == True,
                model.c.owner_id == user_id
            )
        )
    )

    results = await fetch_all(query)

    models_joined = []
    for result in results:
        # Get tasks for this model
        tasks_query = (
            select(task)
            .select_from(
                model_task.join(task, model_task.c.task_id == task.c.id)
            )
            .where(model_task.c.model_id == result["id"])
        )

        tasks_result = await fetch_all(tasks_query)
        tasks = [Task(**task) for task in tasks_result]

        # Construct the joined model
        modality_obj = Modality(
            id=result["modality_id"],
            name=result["modality_name"],
            description=result["modality_description"]
        )

        source_obj = Source(
            id=result["source_id"],
            name=result["source_name"],
            description=result["source_description"],
            created_at=result["source_created_at"]
        )

        programming_language_version_obj = ProgrammingLanguageVersion(
            id=result["pl_version_id"],
            programming_language_id=result["pl_id"],
            version=result["pl_version"],
            created_at=result["pl_version_created_at"]
        )

        model_joined = ModelJoined(
            **result,
            modality=modality_obj,
            source=source_obj,
            programming_language_version=programming_language_version_obj,
            tasks=tasks
        )

        models_joined.append(model_joined)

    if include_integration_jobs:
        # Get integration jobs for all user models
        integration_jobs_by_model = await get_integration_jobs_for_user_models(user_id)

        # Populate integration_jobs for each model
        for model_joined in models_joined:
            model_jobs = integration_jobs_by_model.get(model_joined.id, [])
            model_joined.integration_jobs = [
                JobMetadata(**job) for job in model_jobs]

    return models_joined
