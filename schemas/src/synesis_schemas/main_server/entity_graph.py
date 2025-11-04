import yaml
from uuid import UUID
from typing import List, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# DB Models
# =============================================================================

class DatasetFromDataSourceInDB(BaseModel):
    data_source_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceSupportedInPipelineInDB(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetSupportedInPipelineInDB(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntitySupportedInPipelineInDB(BaseModel):
    model_entity_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInPipelineRunInDB(BaseModel):
    pipeline_run_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDatasetInDB(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputModelEntityInDB(BaseModel):
    pipeline_run_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDataSourceInDB(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInAnalysisInDB(BaseModel):
    id: UUID
    analysis_id: UUID
    model_entity_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# API Models
# =============================================================================

class EdgePoints(BaseModel):
    data_sources: List[UUID] = []
    datasets: List[UUID] = []
    analyses: List[UUID] = []
    pipelines: List[UUID] = []
    model_entities: List[UUID] = []
    pipeline_runs: List[UUID] = []


class GraphNode(BaseModel):
    id: UUID
    name: str
    description: str
    from_entities: EdgePoints
    to_entities: EdgePoints


class PipelineGraphNode(GraphNode):
    id: UUID
    name: str
    description: str
    from_entities: EdgePoints
    runs: List[GraphNode] = []


class EntityGraph(BaseModel):
    data_sources: List[GraphNode] = []
    datasets: List[GraphNode] = []
    pipelines: List[PipelineGraphNode] = []
    analyses: List[GraphNode] = []
    model_entities: List[GraphNode] = []


class EdgePointsUsingNames(BaseModel):
    data_sources: List[str] = []
    datasets: List[str] = []
    analyses: List[str] = []
    pipelines: List[str] = []
    model_entities: List[str] = []
    pipeline_runs: List[str] = []


class GraphNodeUsingNames(GraphNode):
    name: str
    description: str
    from_entities: EdgePointsUsingNames
    to_entities: EdgePointsUsingNames


class PipelineGraphNodeUsingNames(GraphNodeUsingNames):
    id: UUID
    name: str
    description: str
    from_entities: EdgePointsUsingNames
    runs: List[GraphNodeUsingNames] = []


class EntityGraphUsingNames(BaseModel):
    data_sources: List[GraphNodeUsingNames] = []
    datasets: List[GraphNodeUsingNames] = []
    pipelines: List[PipelineGraphNodeUsingNames] = []
    analyses: List[GraphNodeUsingNames] = []
    model_entities: List[GraphNodeUsingNames] = []
    pipeline_runs: List[GraphNodeUsingNames] = []


NODE_TYPE_LITERAL = Literal["data_source", "dataset", "analysis",
                            "pipeline", "model_entity", "pipeline_run"]


class EntityDetail(BaseModel):
    entity_id: UUID
    entity_type: NODE_TYPE_LITERAL
    name: str
    description: str
    inputs: EdgePoints = Field(default_factory=EdgePoints)
    outputs: EdgePoints = Field(default_factory=EdgePoints)


class EntityDetailsResponse(BaseModel):
    entity_details: List[EntityDetail]


# =============================================================================
# Create Models
# =============================================================================


class EdgeDefinition(BaseModel):
    from_node_type: NODE_TYPE_LITERAL
    from_node_id: UUID
    to_node_type: NODE_TYPE_LITERAL
    to_node_id: UUID


class EdgesCreate(BaseModel):
    edges: List[EdgeDefinition]


def get_entity_graph_description(entity_graph: EntityGraph, exclude_ids: bool = True) -> str:
    graph_dict = entity_graph.model_dump(mode="json")

    # Build mapping of UUID to {name}_uuid_{ID} format
    id_to_readable_map = {}

    # Collect all entities with their names and IDs
    def _collect_entities(entities: List[dict], entity_type: str):
        for entity in entities:
            if 'id' in entity and 'name' in entity:
                entity_id = entity['id']
                entity_name = entity['name'].lower().replace(
                    ' ', '_').replace('-', '_')
                # Remove special characters
                entity_name = ''.join(
                    c for c in entity_name if c.isalnum() or c == '_')
                readable_id = f"{entity_name}_UUID_{entity_id}"
                id_to_readable_map[entity_id] = readable_id

            # Handle nested runs in pipelines
            if 'runs' in entity:
                _collect_entities(entity['runs'], 'pipeline_run')

    # Collect from all entity types
    if 'data_sources' in graph_dict:
        _collect_entities(graph_dict['data_sources'], 'data_source')
    if 'datasets' in graph_dict:
        _collect_entities(graph_dict['datasets'], 'dataset')
    if 'pipelines' in graph_dict:
        _collect_entities(graph_dict['pipelines'], 'pipeline')
    if 'analyses' in graph_dict:
        _collect_entities(graph_dict['analyses'], 'analysis')
    if 'model_entities' in graph_dict:
        _collect_entities(graph_dict['model_entities'], 'model_entity')
    if 'pipeline_runs' in graph_dict:
        _collect_entities(graph_dict['pipeline_runs'], 'pipeline_run')

    # Replace IDs with readable format
    def _replace_ids(value: Any) -> Any:
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if k == 'id' and isinstance(v, str) and v in id_to_readable_map:
                    result[k] = id_to_readable_map[v]
                else:
                    result[k] = _replace_ids(v)
            return result
        elif isinstance(value, list):
            return [id_to_readable_map.get(item, _replace_ids(item)) if isinstance(item, str) else _replace_ids(item) for item in value]
        return value

    graph_dict = _replace_ids(graph_dict)

    def _remove_empty_fields(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned = {k: _remove_empty_fields(v) for k, v in value.items()}
            return {k: v for k, v in cleaned.items() if v is not None and v != {} and v != []}
        elif isinstance(value, list):
            cleaned = [_remove_empty_fields(item) for item in value]
            return [item for item in cleaned if item is not None and item != {} and item != []]
        elif not value and value != 0 and value is not False:
            return None
        return value

    graph_dict = _remove_empty_fields(graph_dict)

    # Generate YAML
    yaml_content = yaml.dump(
        graph_dict, sort_keys=False, default_flow_style=False)

    annotations = []
    annotations.append("# Entity Graph Representation")
    annotations.append("#")
    annotations.append(
        "# NOTE: We represent entity IDs in the format {name}_UUID_{ID}.")
    annotations.append(
        "# When submitting data related to a specific entity, use just the ID part after 'UUID_'.")
    annotations.append("#")
    annotations.append("# List of entities in this graph:")

    for readable_id in sorted(id_to_readable_map.values()):
        annotations.append(f"#   - {readable_id}")

    annotations.append("#")
    annotations.append("")

    # Combine annotations and YAML
    return "\n".join(annotations) + yaml_content
