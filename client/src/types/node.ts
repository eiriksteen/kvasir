export type NodeType = "data_source" | "dataset" | "analysis" | "automation";

export interface FrontendNode {
  id: string;
  projectId: string;
  xPosition: number;
  yPosition: number;
  type: NodeType;
  dataSourceId: string | null;
  datasetId: string | null;
  analysisId: string | null; 
  automationId: string | null;
}

export interface FrontendNodeCreate {
  projectId: string;
  xPosition: number | null;
  yPosition: number | null;
  type: NodeType;
  dataSourceId: string | null;
  datasetId: string | null;
  analysisId: string | null; 
  automationId: string | null;
}