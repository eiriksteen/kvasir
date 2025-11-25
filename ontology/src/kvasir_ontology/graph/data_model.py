import yaml
from uuid import UUID
from typing import List, Literal, Any, Tuple, Optional
from datetime import datetime
from pydantic import BaseModel, model_validator

NODE_TYPE_LITERAL = Literal["data_source", "dataset", "analysis",
                            "pipeline", "model_instantiated", "pipeline_run"]


class EntityNodeBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    entity_type: NODE_TYPE_LITERAL
    x_position: float
    y_position: float
    created_at: datetime
    updated_at: datetime


# The node group is quite flexible and functions like a mountpoint into the entity graph
# You can think of it as a project or a folder in a file (entity) system
# A group can correspond to a Python package (projects will)
class NodeGroupBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    python_package_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NodeInGroup(BaseModel):
    node_id: UUID
    node_group_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetFromDataSource(BaseModel):
    data_source_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceSupportedInPipeline(BaseModel):
    data_source_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetSupportedInPipeline(BaseModel):
    dataset_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntitySupportedInPipeline(BaseModel):
    model_instantiated_id: UUID
    pipeline_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInPipelineRun(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInPipelineRun(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelEntityInPipelineRun(BaseModel):
    pipeline_run_id: UUID
    model_instantiated_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDataset(BaseModel):
    pipeline_run_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputModelEntity(BaseModel):
    pipeline_run_id: UUID
    model_instantiated_id: UUID
    created_at: datetime
    updated_at: datetime


class PipelineRunOutputDataSource(BaseModel):
    pipeline_run_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class DataSourceInAnalysis(BaseModel):
    analysis_id: UUID
    data_source_id: UUID
    created_at: datetime
    updated_at: datetime


class DatasetInAnalysis(BaseModel):
    analysis_id: UUID
    dataset_id: UUID
    created_at: datetime
    updated_at: datetime


class ModelInstantiatedInAnalysis(BaseModel):
    analysis_id: UUID
    model_instantiated_id: UUID
    created_at: datetime
    updated_at: datetime


###

class EdgePoints(BaseModel):
    data_sources: List[UUID] = []
    datasets: List[UUID] = []
    analyses: List[UUID] = []
    pipelines: List[UUID] = []
    models_instantiated: List[UUID] = []
    pipeline_runs: List[UUID] = []


class EntityNode(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    x_position: float
    y_position: float
    from_entities: EdgePoints
    to_entities: EdgePoints


# This one is different, outputs go through runs
class PipelineNode(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    x_position: float
    y_position: float
    from_entities: EdgePoints
    runs: List[EntityNode] = []


class EntityGraph(BaseModel):
    data_sources: List[EntityNode] = []
    datasets: List[EntityNode] = []
    pipelines: List[PipelineNode] = []
    analyses: List[EntityNode] = []
    models_instantiated: List[EntityNode] = []


###


class NodeGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    python_package_name: Optional[str] = None


class EntityNodeCreate(BaseModel):
    # Must foreign key to an entity (data source, dataset, analysis, pipeline, model entity)
    id: UUID
    name: str
    entity_type: NODE_TYPE_LITERAL
    x_position: float
    y_position: float
    description: Optional[str] = None
    node_groups: Optional[List[UUID]] = None


# Valid edge types for entity graph
VALID_EDGE_TYPES: List[Tuple[str, str]] = [
    ("data_source", "dataset"),
    ("data_source", "pipeline"),
    ("data_source", "analysis"),
    ("dataset", "pipeline"),
    ("dataset", "analysis"),
    ("model_instantiated", "pipeline"),
    ("model_instantiated", "analysis"),
]

# Valid edge types involving pipeline runs
PIPELINE_RUN_EDGE_TYPES: List[Tuple[str, str]] = [
    ("dataset", "pipeline_run"),
    ("data_source", "pipeline_run"),
    ("model_instantiated", "pipeline_run"),
    ("pipeline_run", "dataset"),
    ("pipeline_run", "model_instantiated"),
    ("pipeline_run", "data_source"),
]


class EdgeDefinition(BaseModel):
    from_node_type: NODE_TYPE_LITERAL
    from_node_id: UUID
    to_node_type: NODE_TYPE_LITERAL
    to_node_id: UUID

    @model_validator(mode='after')
    def validate_edge_type(self) -> 'EdgeDefinition':
        """Validate that this edge uses a valid node type combination."""
        all_valid_edges = VALID_EDGE_TYPES + PIPELINE_RUN_EDGE_TYPES
        edge_type = (self.from_node_type, self.to_node_type)

        if edge_type not in all_valid_edges:
            valid_edges_str = "\n".join(
                [f"  - {from_type} -> {to_type}" for from_type, to_type in all_valid_edges])
            raise ValueError(
                f"Invalid edge type: {self.from_node_type} -> {self.to_node_type}\n\n"
                f"Valid edge types:\n{valid_edges_str}"
            )

        return self


class EdgeDefinitionUsingNames(BaseModel):
    from_node_type: NODE_TYPE_LITERAL
    from_node_name: str
    to_node_type: NODE_TYPE_LITERAL
    to_node_name: str

    @model_validator(mode='after')
    def validate_edge_type(self) -> 'EdgeDefinitionUsingNames':
        """Validate that this edge uses a valid node type combination."""
        all_valid_edges = VALID_EDGE_TYPES + PIPELINE_RUN_EDGE_TYPES
        edge_type = (self.from_node_type, self.to_node_type)

        if edge_type not in all_valid_edges:
            valid_edges_str = "\n".join(
                [f"  - {from_type} -> {to_type}" for from_type, to_type in all_valid_edges])
            raise ValueError(
                f"Invalid edge type: {self.from_node_type} -> {self.to_node_type}\n\n"
                f"Valid edge types:\n{valid_edges_str}"
            )

        return self


def get_entity_graph_description(entity_graph: EntityGraph, include_positions: bool = False) -> str:
    graph_dict = entity_graph.model_dump(mode="json")

    # Build mapping of UUID to {name}_uuid_{ID} format and collect descriptions
    id_to_readable_map = {}
    entity_descriptions = {}  # readable_id -> description

    # Collect all entities with their names, IDs, and descriptions
    def _collect_entities(entities: List[dict]):
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

                # Store description for overview if present
                if 'description' in entity and entity['description']:
                    entity_descriptions[readable_id] = entity['description']

            # Handle nested runs in pipelines
            if 'runs' in entity:
                _collect_entities(entity['runs'])

    # Collect from all entity types
    if 'data_sources' in graph_dict:
        _collect_entities(graph_dict['data_sources'])
    if 'datasets' in graph_dict:
        _collect_entities(graph_dict['datasets'])
    if 'pipelines' in graph_dict:
        _collect_entities(graph_dict['pipelines'])
    if 'analyses' in graph_dict:
        _collect_entities(graph_dict['analyses'])
    if 'models_instantiated' in graph_dict:
        _collect_entities(
            graph_dict['models_instantiated'])
    if 'pipeline_runs' in graph_dict:
        _collect_entities(graph_dict['pipeline_runs'])

    # Replace IDs with readable format
    # Note: model_dump(mode="json") converts UUIDs to strings, so id_to_readable_map uses string keys
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
            # Replace UUID strings in lists (like in EdgePoints)
            # Check if item is a string UUID that needs replacement
            result_list = []
            for item in value:
                if isinstance(item, str) and item in id_to_readable_map:
                    result_list.append(id_to_readable_map[item])
                else:
                    result_list.append(_replace_ids(item))
            return result_list
        return value

    graph_dict = _replace_ids(graph_dict)

    # Filter YAML to only include: id, from_entities, to_entities (and runs for pipelines)
    # Top-level keys (data_sources, datasets, etc.) are kept, but entity nodes are filtered
    def _filter_yaml_fields(value: Any, is_top_level: bool = False, is_edgepoints: bool = False) -> Any:
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                # At top level, keep all entity type keys (data_sources, datasets, etc.)
                if is_top_level:
                    result[k] = _filter_yaml_fields(v, is_top_level=False)
                # For EdgePoints (data_sources, datasets, etc. lists), keep all keys
                elif is_edgepoints:
                    result[k] = _filter_yaml_fields(
                        v, is_top_level=False, is_edgepoints=False)
                # For entity nodes, keep only: id, from_entities, to_entities, runs, and optionally positions
                elif k in ('id', 'from_entities', 'to_entities', 'runs') or (include_positions and k in ('x_position', 'y_position')):
                    if k == 'runs':
                        # Recursively filter nested runs
                        result[k] = _filter_yaml_fields(v, is_top_level=False)
                    elif k in ('from_entities', 'to_entities'):
                        # For EdgePoints, keep all keys (data_sources, datasets, etc.)
                        result[k] = _filter_yaml_fields(
                            v, is_top_level=False, is_edgepoints=True)
                    else:
                        result[k] = _filter_yaml_fields(v, is_top_level=False)
            return result
        elif isinstance(value, list):
            return [_filter_yaml_fields(item, is_top_level=False, is_edgepoints=False) for item in value]
        return value

    graph_dict = _filter_yaml_fields(graph_dict, is_top_level=True)

    if include_positions:
        def _add_position_field(value: Any) -> Any:
            if isinstance(value, dict):
                result = {}
                has_x = 'x_position' in value
                has_y = 'y_position' in value

                for k, v in value.items():
                    if k in ('x_position', 'y_position'):
                        continue
                    else:
                        result[k] = _add_position_field(v)

                if has_x and has_y:
                    result['position'] = f"({value['x_position']}, {value['y_position']})"

                return result
            elif isinstance(value, list):
                return [_add_position_field(item) for item in value]
            return value

        graph_dict = _add_position_field(graph_dict)

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

    # Create entities overview as YAML (name/id: description format)
    entities_dict = {}
    for readable_id in sorted(id_to_readable_map.values()):
        entities_dict[readable_id] = entity_descriptions.get(readable_id, "")

    entities_yaml = yaml.dump(
        {"entities": entities_dict}, sort_keys=False, default_flow_style=False, allow_unicode=True)

    graph_yaml = yaml.dump(
        {"graph": graph_dict}, sort_keys=False, default_flow_style=False)

    annotations = []
    annotations.append("# Entity Graph Representation")
    annotations.append("#")
    annotations.append(
        "# NOTE: We represent entity IDs in the format {name}_UUID_{ID}.")
    annotations.append(
        "# When submitting data related to a specific entity, use just the ID part after 'UUID_'.")
    annotations.append("")

    return "\n".join(annotations) + entities_yaml + "\n" + graph_yaml
