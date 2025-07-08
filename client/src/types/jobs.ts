export interface Job {
	id: string;
	jobName: string;
	type: string;
	status: string;
	startedAt: string;
	completedAt: string | null;
}

export type JobCategory = "integration" | "analysis" | "automation";

export type IntegrationSource = "local" | "aws" | "azure" | "gcp";

export interface IntegrationJobInput {
  files: File[];
  dataDescription: string;
  dataSource: IntegrationSource;
  type: "integration";
}

export interface ModelIntegrationJobInput {
  modelId: string;
  source: "github" | "pip";
  type: "model_integration";
}

export interface AnalysisJobInput {
  jobId: string;
  type: "analysis";
}

export interface AutomationJobInput {
  jobId: string;
  type: "automation";
}