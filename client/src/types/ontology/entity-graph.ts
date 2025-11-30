import { UUID } from "crypto";

export type NodeType = 
  | "data_source"
  | "dataset"
  | "analysis"
  | "pipeline"
  | "model_instantiated"
  | "pipeline_run";

export type GraphNodeType = "leaf" | "branch";
export type EntityType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_instantiated";
export type BranchType = EntityType | "mixed";

// Base Models

export interface NodeBase {
  id: UUID;
  name: string;
  description?: string | null;
  nodeType: GraphNodeType;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface LeafNodeBase {
  id: UUID;
  entityId: UUID;
  entityType: NodeType;
  createdAt: string;
  updatedAt: string;
}

export interface BranchNodeBase {
  id: UUID;
  name: string;
  description?: string | null;
  pythonPackageName?: string | null;
  createdAt: string;
  updatedAt: string;
}

// Entity Links Model
export interface EntityLinks {
  dataSources: UUID[];
  datasets: UUID[];
  analyses: UUID[];
  pipelines: UUID[];
  modelsInstantiated: UUID[];
}

// Composite Models

export interface LeafNode extends NodeBase, LeafNodeBase {
  nodeType: "leaf";
  fromEntities: EntityLinks;
  toEntities: EntityLinks;
}

export interface PipelineNode extends NodeBase, LeafNodeBase {
  nodeType: "leaf";
  entityType: "pipeline";
  fromEntities: EntityLinks;
  runs: LeafNode[];
}

export interface BranchNode extends NodeBase, BranchNodeBase {
  nodeType: "branch";
  branchType: BranchType;
  children: (LeafNode | PipelineNode | BranchNode)[];
}

export type GraphNode = LeafNode | PipelineNode | BranchNode;

export interface EntityGraph {
  dataSources: (LeafNode | BranchNode)[];
  datasets: (LeafNode | BranchNode)[];
  pipelines: (LeafNode | PipelineNode | BranchNode)[];
  analyses: (LeafNode | BranchNode)[];
  modelsInstantiated: (LeafNode | BranchNode)[];
}

// Create Models

export interface LeafNodeCreate {
  entityId: UUID;
  name: string;
  entityType: NodeType;
  xPosition: number;
  yPosition: number;
  description?: string | null;
  parentBranchNodes?: UUID[] | null;
  fromEntities?: UUID[] | null;
  toEntities?: UUID[] | null;
}

export interface BranchNodeCreate {
  name: string;
  xPosition: number;
  yPosition: number;
  description?: string | null;
  pythonPackageName?: string | null;
  parentBranchNodes?: UUID[] | null;
  children?: (BranchNodeCreate | LeafNodeCreate)[] | null;
}


// Valid edge types for entity graph
export const VALID_EDGE_TYPES: [string, string][] = [
  ["data_source", "dataset"],
  ["data_source", "pipeline"],
  ["data_source", "analysis"],
  ["dataset", "pipeline"],
  ["dataset", "analysis"],
  ["model_instantiated", "pipeline"],
  ["model_instantiated", "analysis"],
];

// Valid edge types involving pipeline runs
export const PIPELINE_RUN_EDGE_TYPES: [string, string][] = [
  ["dataset", "pipeline_run"],
  ["data_source", "pipeline_run"],
  ["model_instantiated", "pipeline_run"],
  ["pipeline_run", "dataset"],
  ["pipeline_run", "model_instantiated"],
  ["pipeline_run", "data_source"],
];

export interface EdgeDefinition {
  fromNodeType: NodeType;
  fromNodeId: UUID;
  toNodeType: NodeType;
  toNodeId: UUID;
}

export interface EdgeDefinitionUsingNames {
  fromNodeType: NodeType;
  fromNodeName: string;
  toNodeType: NodeType;
  toNodeName: string;
}

