export interface Job {
	id: string;
	type: string;
	status: string;
	startedAt: string;
	completedAt: string | null;
}

export type JobCategory = "integration" | "analysis" | "automation";


export interface IntegrationJobInput {
  file: File;
  data_description: string;
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