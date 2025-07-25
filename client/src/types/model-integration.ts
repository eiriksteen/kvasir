
export type ModelIntegrationJobInput = {
  modelId: string;
  source: "github" | "pip";
  type: "model_integration";
  createdAt: string;
  updatedAt: string;
}

export type ModelIntegrationJobResult = {
  modelId: string;
  jobId: string;
  createdAt: string;
  updatedAt: string;
}