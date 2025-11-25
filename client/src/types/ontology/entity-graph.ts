import { UUID } from "crypto";

export type NodeType = 
  | "data_source"
  | "dataset"
  | "analysis"
  | "pipeline"
  | "model_instantiated"
  | "pipeline_run";

// Base Models

export interface EntityNodeBase {
  id: UUID;
  name: string;
  entityType: NodeType;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface NodeGroupBase {
  id: UUID;
  name: string;
  description?: string | null;
  pythonPackageName?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface NodeInGroup {
  nodeId: UUID;
  nodeGroupId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetFromDataSource {
  dataSourceId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceSupportedInPipeline {
  dataSourceId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetSupportedInPipeline {
  datasetId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntitySupportedInPipeline {
  modelInstantiatedId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetInPipelineRun {
  pipelineRunId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceInPipelineRun {
  pipelineRunId: UUID;
  dataSourceId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityInPipelineRun {
  pipelineRunId: UUID;
  modelInstantiatedId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputDataset {
  pipelineRunId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputModelEntity {
  pipelineRunId: UUID;
  modelInstantiatedId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputDataSource {
  pipelineRunId: UUID;
  dataSourceId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceInAnalysis {
  analysisId: UUID;
  dataSourceId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetInAnalysis {
  analysisId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelInstantiatedInAnalysis {
  analysisId: UUID;
  modelInstantiatedId: UUID;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface EdgePoints {
  dataSources: UUID[];
  datasets: UUID[];
  analyses: UUID[];
  pipelines: UUID[];
  modelsInstantiated: UUID[];
  pipelineRuns: UUID[];
}

export interface EntityNode {
  id: UUID;
  name: string;
  description?: string | null;
  xPosition: number;
  yPosition: number;
  fromEntities: EdgePoints;
  toEntities: EdgePoints;
}

export interface PipelineNode extends EntityNode {
  id: UUID;
  description?: string | null;
  xPosition: number;
  yPosition: number;
  fromEntities: EdgePoints;
  runs: EntityNode[];
}

export interface EntityGraph {
  dataSources: EntityNode[];
  datasets: EntityNode[];
  pipelines: PipelineNode[];
  analyses: EntityNode[];
  modelsInstantiated: EntityNode[];
}

// Create Models

export interface NodeGroupCreate {
  name: string;
  description?: string | null;
  pythonPackageName?: string | null;
}

export interface EntityNodeCreate {
  id: UUID;
  name: string;
  entityType: NodeType;
  xPosition: number;
  yPosition: number;
  description?: string | null;
  nodeGroups?: UUID[] | null;
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

