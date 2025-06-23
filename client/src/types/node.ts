export type NodeType = "dataset" | "analysis" | "automation";

export interface FrontendNode {
  id: string;
  projectId: string;
  xPosition: number;
  yPosition: number;
  type: NodeType;
  datasetId: string | null;
  analysisId: string | null; 
  automationId: string | null;
}

export interface FrontendNodeCreate {
  projectId: string;
  xPosition: number;
  yPosition: number;
  type: NodeType;
  datasetId: string | null;
  analysisId: string | null; 
  automationId: string | null;
}