export interface Job {
	id: string;
	jobName: string;
	type: string;
	status: string;
	startedAt: string;
	completedAt: string | null;
}

export type JobCategory = "integration" | "analysis" | "automation";

export type IntegrationSource = "directory" | "aws" | "azure" | "gcp";

export interface IntegrationJobInput {
  files: File[];
  data_description: string;
  data_source: IntegrationSource;
  type: "integration";
}

export interface AnalysisJobInput {
  job_id: string;
  type: "analysis";
}

export interface AutomationJobInput {
  job_id: string;
  type: "automation";
}