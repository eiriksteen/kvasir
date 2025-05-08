export interface AnalysisStep {
    stepName: string;
    stepDescription: string;
}

export interface AnalysisPlan {
    analysisOverview: string;
    analysisPlan: AnalysisStep[];
}

export interface AnalysisJobResultMetadata {
    jobId: string;
    datasetIds: string[];
    automationIds: string[];
    analysisPlan: AnalysisPlan;
    numberOfDatasets: number;
    numberOfAutomations: number;
    createdAt: string;
    pdfCreated: boolean;
}

export interface Analysises {
    analysisJobResults: AnalysisJobResultMetadata[];
}