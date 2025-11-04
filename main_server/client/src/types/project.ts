import { UUID } from "crypto";
import { EntityGraph } from "./entity-graph";

export type EntityType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";
export type NodeType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";

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

// API Models

export interface ProjectNodes {
  projectDataSources: ProjectDataSourceInDB[];
  projectDatasets: ProjectDatasetInDB[];
  projectPipelines: ProjectPipelineInDB[];
  projectAnalyses: ProjectAnalysisInDB[];
  projectModelEntities: ProjectModelEntityInDB[];
}

export interface Project extends ProjectInDB {
  graph: EntityGraph;
  projectNodes: ProjectNodes;
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

export interface UpdateNodePosition {
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
