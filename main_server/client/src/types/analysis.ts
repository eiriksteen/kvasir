import { UUID } from "crypto";

export interface AnalysisStep {
    stepName: string;
    stepDescription: string;
}

export interface AnalysisPlan {
    analysisOverview: string;
    analysisPlan: AnalysisStep[];
}

export interface AnalysisStatusMessage {
    id: UUID;
    jobId: UUID;
    type: 'tool_call' | 'tool_result' | 'analysis_result' | 'user_prompt';
    message: string;
    createdAt: string;
}

export interface AnalysisJobResultMetadata {
    jobId: UUID;
    name: string;
    datasetIds: UUID[];
    pipelineIds: UUID[];
    analysisPlan: AnalysisPlan;
    numberOfDatasets: number;
    numberOfPipelines: number;
    createdAt: string;
    pdfCreated: boolean;
    statusMessages: AnalysisStatusMessage[];
}

export interface AnalysisRequest {
    projectId: UUID;
    datasetIds: UUID[];
    analysisIds: UUID[];
    pipelineIds: UUID[];
    prompt: string | null;
    conversationId: UUID;
}