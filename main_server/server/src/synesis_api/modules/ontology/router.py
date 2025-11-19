import io
import json
from typing import Annotated, List, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, Form
from pydantic import BaseModel, Field

from synesis_api.auth.service import get_current_user, oauth2_scheme
from synesis_api.auth.schema import User
from synesis_api.modules.ontology.service import create_ontology_for_user

from kvasir_ontology.graph.data_model import EntityGraph, NODE_TYPE_LITERAL, EdgeDefinition
from kvasir_ontology.entities.data_source.data_model import DataSource, DataSourceCreate
from kvasir_ontology.entities.dataset.data_model import Dataset, DatasetCreate
from kvasir_ontology.entities.pipeline.data_model import Pipeline, PipelineCreate
from kvasir_ontology.entities.model.data_model import ModelInstantiated, ModelInstantiatedCreate
from kvasir_ontology.entities.analysis.data_model import Analysis, AnalysisCreate


from kvasir_research.agents.v1.extraction.agent import run_extraction_agent

router = APIRouter()


# Request models for insert operations
class DataSourceInsertRequest(BaseModel):
    data_source: DataSourceCreate
    edges: List[EdgeDefinition] = Field(default_factory=list)


class DatasetInsertRequest(BaseModel):
    dataset: DatasetCreate
    edges: List[EdgeDefinition] = Field(default_factory=list)


class AnalysisInsertRequest(BaseModel):
    analysis: AnalysisCreate
    edges: List[EdgeDefinition] = Field(default_factory=list)


class PipelineInsertRequest(BaseModel):
    pipeline: PipelineCreate
    edges: List[EdgeDefinition] = Field(default_factory=list)


class ModelInstantiatedInsertRequest(BaseModel):
    model_instantiated: ModelInstantiatedCreate
    edges: List[EdgeDefinition] = Field(default_factory=list)


@router.post("/{mount_group_id}/data-source", response_model=DataSource)
async def insert_data_source_endpoint(
    mount_group_id: UUID,
    request: DataSourceInsertRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> DataSource:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.insert_data_source(request.data_source, request.edges)


@router.post("/{mount_group_id}/dataset", response_model=Dataset)
async def insert_dataset_endpoint(
    mount_group_id: UUID,
    request: DatasetInsertRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Dataset:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.insert_dataset(request.dataset, request.edges)


@router.post("/{mount_group_id}/analysis", response_model=Analysis)
async def insert_analysis_endpoint(
    mount_group_id: UUID,
    request: AnalysisInsertRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Analysis:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.insert_analysis(request.analysis, request.edges)


@router.post("/{mount_group_id}/pipeline", response_model=Pipeline)
async def insert_pipeline_endpoint(
    mount_group_id: UUID,
    request: PipelineInsertRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> Pipeline:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.insert_pipeline(request.pipeline, request.edges)


@router.post("/{mount_group_id}/model-instantiated", response_model=ModelInstantiated)
async def insert_model_instantiated_endpoint(
    mount_group_id: UUID,
    request: ModelInstantiatedInsertRequest,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ModelInstantiated:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.insert_model_instantiated(request.model_instantiated, request.edges)


@router.post("/{mount_group_id}/files-data-sources", response_model=List[DataSource])
async def insert_files_data_sources_endpoint(
    mount_group_id: UUID,
    files: List[UploadFile],
    edges: Annotated[str, Form()] = "[]",
    user: Annotated[User, Depends(get_current_user)] = None,
    token: str = Depends(oauth2_scheme)
) -> List[DataSource]:

    ontology = create_ontology_for_user(
        user.id, mount_group_id, bearer_token=token)
    file_bytes = [io.BytesIO(await file.read()) for file in files]
    file_names = [file.filename for file in files]

    try:
        edges_list = json.loads(edges) if edges else []
        edges_parsed = [EdgeDefinition(
            **edge) if isinstance(edge, dict) else edge for edge in edges_list]
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid edges format: {str(e)}")

    file_objs, file_paths = await ontology.insert_files_data_sources(file_bytes, file_names, edges_parsed)

    if file_paths:
        group_info = await ontology.graph.get_node_group(mount_group_id)

        await run_extraction_agent.kiq(
            "We have added new files at the paths: " +
            ", ".join([file_path.as_posix() for file_path in file_paths]) +
            ". Add the file details. ",
            user_id=user.id,
            project_id=mount_group_id,
            package_name=group_info.python_package_name,
            sandbox_type="modal",
            bearer_token=token
        )

    return file_objs


@router.delete("/{mount_group_id}/data-source/{data_source_id}")
async def delete_data_source_endpoint(
    mount_group_id: UUID,
    data_source_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    await ontology.delete_data_source(data_source_id)
    return f"Data source deleted successfully: {data_source_id}"


@router.delete("/{mount_group_id}/dataset/{dataset_id}")
async def delete_dataset_endpoint(
    mount_group_id: UUID,
    dataset_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    await ontology.delete_dataset(dataset_id)
    return f"Dataset deleted successfully: {dataset_id}"


@router.delete("/{mount_group_id}/model-instantiated/{model_instantiated_id}")
async def delete_model_entity_endpoint(
    mount_group_id: UUID,
    model_instantiated_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    await ontology.delete_model(model_instantiated_id)
    return f"Model entity deleted successfully: {model_instantiated_id}"


@router.get("/{mount_group_id}/data-sources", response_model=List[DataSource])
async def get_mounted_data_sources_endpoint(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[DataSource]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_mounted_data_sources()


@router.get("/{mount_group_id}/datasets", response_model=List[Dataset])
async def get_mounted_datasets_endpoint(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Dataset]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_mounted_datasets()


@router.get("/{mount_group_id}/pipelines", response_model=List[Pipeline])
async def get_mounted_pipelines_endpoint(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Pipeline]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_mounted_pipelines()


@router.get("/{mount_group_id}/models-instantiated", response_model=List[ModelInstantiated])
async def get_mounted_models_instantiated_endpoint(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[ModelInstantiated]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_mounted_models_instantiated()


@router.get("/{mount_group_id}/analyses", response_model=List[Analysis])
async def get_mounted_analyses_endpoint(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Analysis]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_mounted_analyses()


@router.delete("/{mount_group_id}/pipeline/{pipeline_id}")
async def delete_pipeline_endpoint(
    mount_group_id: UUID,
    pipeline_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    await ontology.delete_pipeline(pipeline_id)
    return f"Pipeline deleted successfully: {pipeline_id}"


@router.delete("/{mount_group_id}/analysis/{analysis_id}")
async def delete_analysis_endpoint(
    mount_group_id: UUID,
    analysis_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    await ontology.delete_analysis(analysis_id)
    return f"Analysis deleted successfully: {analysis_id}"


@router.get("/{mount_group_id}/entity-graph", response_model=EntityGraph)
async def get_entity_graph(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> EntityGraph:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_entity_graph()


@router.get("/{mount_group_id}/entities", response_model=List[Union[DataSource, Dataset, Pipeline, ModelInstantiated, Analysis]])
async def get_entities(
    mount_group_id: UUID,
    entity_ids: List[UUID] = Query(...,
                                   description="List of entity IDs to retrieve"),
    user: Annotated[User, Depends(get_current_user)] = None
) -> List[Union[DataSource, Dataset, Pipeline, ModelInstantiated, Analysis]]:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    return await ontology.get_entities(entity_ids)


@router.get("/{mount_group_id}/describe-entity-graph")
async def describe_entity_graph(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    description = await ontology.describe_entity_graph()
    return description


@router.get("/{mount_group_id}/describe-entity/entities/{entity_id}")
async def describe_entity(
    mount_group_id: UUID,
    entity_id: UUID,
    entity_type: NODE_TYPE_LITERAL = Query(..., description="Entity type"),
    include_connections: bool = Query(
        True, description="Include connections in description"),
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    try:
        description = await ontology.describe_entity(entity_id, entity_type, include_connections)
        return description
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{mount_group_id}/describe-mount-group")
async def describe_mount_group(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None
) -> str:
    ontology = create_ontology_for_user(user.id, mount_group_id)
    try:
        description = await ontology.describe_mount_group()
        return description
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{mount_group_id}/run-extraction")
async def run_extraction(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)] = None,
    token: str = Depends(oauth2_scheme)
) -> str:

    ontology = create_ontology_for_user(
        user.id, mount_group_id, bearer_token=token)
    node_group = await ontology.graph.get_node_group(mount_group_id)

    if not node_group:
        raise HTTPException(status_code=404, detail="Project not found")

    await run_extraction_agent.kiq(
        "Scan the codebase to update the entity graph. Add any new entities, remove any no longer relevant, add new edges between entities, or remove any edges that are no longer relevant. Ensure the graph accurately represents the current state of the project. ",
        user_id=user.id,
        project_id=mount_group_id,
        package_name=node_group.python_package_name,
        sandbox_type="modal",
        bearer_token=token
    )

    return "Extraction task started"
