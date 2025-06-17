export interface AnalysisStep {
    stepName: string;
    stepDescription: string;
}

export interface AnalysisPlan {
    analysisOverview: string;
    analysisPlan: AnalysisStep[];
}

export interface AnalysisStatusMessage {
    id: string;
    jobId: string;
    type: 'tool_call' | 'tool_result' | 'analysis_result' | 'user_prompt';
    message: string;
    createdAt: string;
}

export interface AnalysisJobResultMetadata {
    jobId: string;
    name: string;
    datasetIds: string[];
    automationIds: string[];
    analysisPlan: AnalysisPlan;
    numberOfDatasets: number;
    numberOfAutomations: number;
    createdAt: string;
    pdfCreated: boolean;
    statusMessages: AnalysisStatusMessage[];
}

export interface Analyses {
    analysesJobResults: AnalysisJobResultMetadata[];
}

export interface AnalysisRequest {
    projectId: string;
    datasetIds: string[];
    analysisIds: string[];
    automationIds: string[];
    prompt: string | null;
    conversationId: string;
}