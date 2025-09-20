import { UUID } from "crypto";

export type NodeType = "data_source" | "model_source" | "dataset" | "analysis" | "pipeline" | "model";

export interface FrontendNode {
  id: UUID;
  projectId: UUID;
  xPosition: number;
  yPosition: number;
  type: NodeType;
  dataSourceId: UUID | null;
  modelSourceId: UUID | null;
  datasetId: UUID | null;
  analysisId: UUID | null; 
  pipelineId: UUID | null;
  modelId: UUID | null;
}

export interface FrontendNodeCreate {
  projectId: UUID;
  xPosition: number | null;
  yPosition: number | null;
  type: NodeType;
  dataSourceId: UUID | null;
  modelSourceId: UUID | null;
  datasetId: UUID | null;
  analysisId: UUID | null; 
  pipelineId: UUID | null;
  modelId: UUID | null;
}