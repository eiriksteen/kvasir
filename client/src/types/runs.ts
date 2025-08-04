import { UUID } from "crypto";

export type Run = {
	id: UUID;
	type: 'data_integration' | 'analysis' | 'automation';
	status: 'pending' | 'running' | 'completed' | 'failed';
	userId: UUID;
	conversationId: UUID;
	startedAt: string;
	completedAt: string | null;
	runName: string | null;
	input: RunInput | null;
    result: RunResult | null;
}


export type RunMessage = {
	id: UUID;
	content: string;
	runId: UUID;
	type: 'tool_call' | 'result' | 'error';
	createdAt: string;
}


export type DataIntegrationRunInput = {
	runId: UUID;
	targetDatasetDescription: string;
	dataSourceIds: UUID[];
	createdAt: string;
}


export type ModelIntegrationRunInput = {
	runId: UUID;
	modelIdStr: UUID;
	source: 'github' | 'pip' | 'source_code';
	createdAt: string;
}

export type DataIntegrationRunResult = {
	runId: UUID;
	datasetId: UUID;
	codeExplanation: string;
	pythonCodePath: string;
	createdAt: string;
}

export type ModelIntegrationRunResult = {
	runId: UUID;
	modelId: UUID;
	createdAt: string;
}

export type RunInput = DataIntegrationRunInput | ModelIntegrationRunInput;
export type RunResult = DataIntegrationRunResult | ModelIntegrationRunResult;




