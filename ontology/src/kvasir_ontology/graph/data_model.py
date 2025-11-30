import yaml
from uuid import UUID
from typing import List, Literal, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


NODE_TYPE_LITERAL = Literal["leaf", "branch"]
CHILD_TYPE_LITERAL = Literal["data_source", "dataset", "analysis",
                             "pipeline", "model_instantiated", "pipeline_run"]
BRANCH_TYPE_LITERAL = Literal["data_source", "dataset", "analysis",
                              "pipeline", "model_instantiated", "mixed"]


class NodeBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    node_type: NODE_TYPE_LITERAL
    x_position: float
    y_position: float
    created_at: datetime
    updated_at: datetime


class LeafNodeBase(BaseModel):
    id: UUID
    # Foreign key to an entity
    entity_id: UUID
    entity_type: CHILD_TYPE_LITERAL
    created_at: datetime
    updated_at: datetime


# The branch node is quite flexible and functions like a mountpoint into the entity graph
# You can think of it as a project or a folder in a file (entity) system
# A branch can correspond to a Python package (projects will)
class BranchNodeBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    python_package_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ParentChildRelation(BaseModel):
    child_id: UUID
    parent_id: UUID
    created_at: datetime
    updated_at: datetime


class EdgeBase(BaseModel):
    # Both IDs are foreign keys to child nodes (not branch nodes) since we track relations between entities and not groups
    # (group edges are defined as the union of in/out edges)
    from_entity_id: UUID
    to_entity_id: UUID
    created_at: datetime
    updated_at: datetime


###


class EntityLinks(BaseModel):
    data_sources: List[UUID] = Field(default_factory=list)
    datasets: List[UUID] = Field(default_factory=list)
    analyses: List[UUID] = Field(default_factory=list)
    pipelines: List[UUID] = Field(default_factory=list)
    models_instantiated: List[UUID] = Field(default_factory=list)


class LeafNode(NodeBase, LeafNodeBase):
    from_entities: EntityLinks = Field(default_factory=EntityLinks)
    to_entities: EntityLinks = Field(default_factory=EntityLinks)


# This one is different, outputs go through runs
class PipelineNode(NodeBase, LeafNodeBase):
    from_entities: EntityLinks = Field(default_factory=EntityLinks)
    runs: List[LeafNode] = Field(default_factory=list)


class BranchNode(NodeBase, BranchNodeBase):
    branch_type: BRANCH_TYPE_LITERAL
    children: List[Union[LeafNode, PipelineNode, 'BranchNode']
                   ] = Field(default_factory=list)


class EntityGraph(BaseModel):
    # For now, we enforce all nodes in a group to be of the same entity type
    # However all data models except EntityGraph accomodate multiple types so this can easily be changed
    data_sources: List[Union[BranchNode, LeafNode]]
    datasets: List[Union[BranchNode, LeafNode]]
    pipelines: List[Union[BranchNode, LeafNode, PipelineNode]]
    analyses: List[Union[BranchNode, LeafNode]]
    models_instantiated: List[Union[BranchNode, LeafNode]]


###


class LeafNodeCreate(BaseModel):
    # Must foreign key to an entity (data source, dataset, analysis, pipeline, model entity)
    entity_id: UUID
    name: str
    entity_type: CHILD_TYPE_LITERAL
    x_position: float
    y_position: float
    description: Optional[str] = None
    parent_branch_nodes: Optional[List[UUID]] = None
    from_entities: Optional[List[UUID]] = None
    to_entities: Optional[List[UUID]] = None


class BranchNodeCreate(BaseModel):
    name: str
    x_position: float
    y_position: float
    description: Optional[str] = None
    python_package_name: Optional[str] = None
    parent_branch_nodes: Optional[List[UUID]] = None
    children: Optional[List[Union['BranchNodeCreate', LeafNodeCreate]]] = None


class EdgeCreate(BaseModel):
    from_entity_id: UUID
    to_entity_id: UUID

##


def branch_node_to_entity_graph(branch: BranchNode) -> EntityGraph:
    data_sources = []
    datasets = []
    pipelines = []
    models_instantiated = []
    analyses = []

    entity_map = {
        "data_source": data_sources,
        "dataset": datasets,
        "pipeline": pipelines,
        "model_instantiated": models_instantiated,
        "analysis": analyses
    }

    for child in branch.children:
        if child.node_type == "leaf":
            entity_map[child.entity_type].append(child)
        else:
            if child.branch_type == "mixed":
                raise ValueError(
                    f"Currently all groups in entity graph must be of the same type. {child} is a mixed branch")
            entity_map[child.branch_type].append(child)

    out = EntityGraph(
        data_sources=entity_map["data_source"],
        datasets=entity_map["dataset"],
        pipelines=entity_map["pipeline"],
        models_instantiated=entity_map["model_instantiated"],
        analyses=entity_map["analysis"]
    )

    return out


def get_entity_graph_description(entity_graph: EntityGraph, include_positions: bool = False) -> str:

    def _get_entity_map():
        branch_id_to_name = {}
        entity_id_to_full_id = {}
        entities_overview = []

        def _process_node(node: Union[Union[LeafNode, PipelineNode], BranchNode]):
            if node.node_type == "leaf":
                full_id = f"{node.name}__uuid__{node.entity_id}"
                entity_id_to_full_id[node.entity_id] = full_id
                entities_overview.append({"full_id": full_id})

                if node.entity_type == "pipeline":
                    for run_obj in node.runs:
                        _process_node(run_obj)
            else:
                branch_id_to_name[node.id] = node.name
                for child_node in node.children:
                    _process_node(child_node)

        for root_node in (entity_graph.data_sources + entity_graph.datasets +
                          entity_graph.pipelines + entity_graph.models_instantiated +
                          entity_graph.analyses):
            _process_node(root_node)

        return branch_id_to_name, entity_id_to_full_id, entities_overview

    branch_id_to_name, entity_id_to_full_id, entities_overview = _get_entity_map()

    def _get_entity_graph_dict():
        def _process_node(node: Union[Union[LeafNode, PipelineNode], BranchNode]):
            if node.node_type == "leaf":
                from_dict = {
                    k: [entity_id_to_full_id[entity_id]
                        for entity_id in v]
                    for k, v in [
                        ("data_sources", node.from_entities.data_sources),
                        ("datasets", node.from_entities.datasets),
                        ("models_instantiated",
                         node.from_entities.models_instantiated),
                        ("analyses", node.from_entities.analyses),
                        ("pipelines", node.from_entities.pipelines),
                    ]
                    if v
                }

                out_dict = {
                    "id": entity_id_to_full_id[node.entity_id],
                    **({"description": node.description} if node.description else {}),
                    **({"position": [node.x_position, node.y_position]} if include_positions else {}),
                    **({"from": from_dict} if from_dict else {}),
                }

                if node.entity_type == "pipeline":
                    runs_list = [_process_node(run_obj)
                                 for run_obj in node.runs]
                    return {
                        **out_dict,
                        **({"runs": runs_list} if runs_list else {}),
                    }
                else:
                    to_dict = {
                        k: [entity_id_to_full_id[entity_id]
                            for entity_id in v]
                        for k, v in [
                            ("data_sources", node.to_entities.data_sources),
                            ("datasets", node.to_entities.datasets),
                            ("models_instantiated",
                             node.to_entities.models_instantiated),
                            ("analyses", node.to_entities.analyses),
                            ("pipelines", node.to_entities.pipelines),
                        ]
                        if v
                    }

                    if to_dict:
                        out_dict["to"] = to_dict

                    return out_dict
            else:
                return {
                    "group": branch_id_to_name[node.id],
                    "description": node.description,
                    "children": [_process_node(child_node) for child_node in node.children]
                }
        return {
            "data_sources": [_process_node(node_obj) for node_obj in entity_graph.data_sources],
            "datasets": [_process_node(node_obj) for node_obj in entity_graph.datasets],
            "pipelines":  [_process_node(node_obj) for node_obj in entity_graph.pipelines],
            "models_instantiated": [_process_node(node_obj) for node_obj in entity_graph.models_instantiated],
            "analyses": [_process_node(node_obj) for node_obj in entity_graph.analyses],
        }

    entity_graph_dict = _get_entity_graph_dict()

    entities_overview_yaml = yaml.dump(
        entities_overview, default_flow_style=False, sort_keys=False)
    entity_graph_yaml = yaml.dump(
        entity_graph_dict, default_flow_style=False, sort_keys=False)

    desc = (
        "<entity_graph>\n\n" +
        f"The following is a list of all entities in the entity graph. All IDs are represented as [node_name]_uuid_[entity_uuid]. Use the entity UUID when referring to the entities in tool calls\n\n" +
        f"{entities_overview_yaml}\n\n" +
        f"The following is the entity graph.\n\n" +
        f"{entity_graph_yaml}\n\n" +
        "</entity_graph>"
    )

    return desc
