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
    numberOfDatasets: number;
    numberOfAutomations: number;
    analysisPlan: AnalysisPlan;
    createdAt: string;
    pdfCreated: boolean;
}

export interface Analysises {
    analysisJobResults: AnalysisJobResultMetadata[];
}