import { UUID } from "crypto";

export type EntityType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";

// DB Models

export interface ProjectInDB {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  pythonPackageName: string;
  viewPortX: number;
  viewPortY: number;
  viewPortZoom: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectDataSourceInDB {
  projectId: UUID;
  dataSourceId: UUID;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectDatasetInDB {
  projectId: UUID;
  datasetId: UUID;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectAnalysisInDB {
  projectId: UUID;
  analysisId: UUID;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectPipelineInDB {
  projectId: UUID;
  pipelineId: UUID;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectModelEntityInDB {
  projectId: UUID;
  modelEntityId: UUID;
  xPosition: number;
  yPosition: number;
  createdAt: string;
  updatedAt: string;
}

// Graph Types

export type GraphNodeConnections = {
  fromDataSources: UUID[];
  fromDatasets: UUID[];
  fromAnalyses: UUID[];
  fromPipelines: UUID[];
  fromModelEntities: UUID[];
  toDataSources: UUID[];
  toDatasets: UUID[];
  toAnalyses: UUID[];
  toPipelines: UUID[];
  toModelEntities: UUID[];
}

export type DataSourceInGraph = {
  id: UUID;
  name: string;
  type: string;
  briefDescription: string;
  xPosition: number;
  yPosition: number;
  connections: GraphNodeConnections;
}

export type DatasetInGraph = {
  id: UUID;
  name: string;
  briefDescription: string;
  xPosition: number;
  yPosition: number;
  connections: GraphNodeConnections;
}

export type PipelineInGraph = {
  id: UUID;
  name: string;
  briefDescription: string;
  xPosition: number;
  yPosition: number;
  connections: GraphNodeConnections;
}

export type AnalysisInGraph = {
  id: UUID;
  name: string;
  briefDescription: string;
  xPosition: number;
  yPosition: number;
  connections: GraphNodeConnections;
}

export type ModelEntityInGraph = {
  id: UUID;
  name: string;
  briefDescription: string;
  xPosition: number;
  yPosition: number;
  connections: GraphNodeConnections;
}

export type ProjectGraph = {
  dataSources: DataSourceInGraph[];
  datasets: DatasetInGraph[];
  pipelines: PipelineInGraph[];
  analyses: AnalysisInGraph[];
  modelEntities: ModelEntityInGraph[];
}

// API Models

export interface Project extends ProjectInDB {
  graph: ProjectGraph;
}

// Create Models

export interface ProjectCreate {
  name: string;
  description: string;
  pythonPackageName?: string | null;
}

export interface ProjectDetailsUpdate {
  projectId: UUID;
  name?: string | null;
  description?: string | null;
}

export interface EntityPositionCreate {
  x: number;
  y: number;
}

export interface AddEntityToProject {
  projectId: UUID;
  entityType: EntityType;
  entityId: UUID;
}

export interface RemoveEntityFromProject {
  projectId: UUID;
  entityType: EntityType;
  entityId: UUID;
}

export interface UpdateEntityPosition {
  projectId: UUID;
  entityType: EntityType;
  entityId: UUID;
  xPosition: number;
  yPosition: number;
}

export interface UpdateProjectViewport {
  projectId: UUID;
  x: number;
  y: number;
  zoom: number;
}
