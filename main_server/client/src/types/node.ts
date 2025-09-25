import { UUID } from "crypto";

export type NodeType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";

export interface FrontendNode {
  id: UUID;
  projectId: UUID;
  xPosition: number;
  yPosition: number;
  type: NodeType;
  dataSourceId: UUID | null;
  datasetId: UUID | null;
  analysisId: UUID | null; 
  pipelineId: UUID | null;
  modelEntityId: UUID | null;
}

export interface FrontendNodeCreate {
  projectId: UUID;
  xPosition: number | null;
  yPosition: number | null;
  type: NodeType;
  dataSourceId: UUID | null;
  datasetId: UUID | null;
  analysisId: UUID | null; 
  pipelineId: UUID | null;
  modelEntityId: UUID | null;
}