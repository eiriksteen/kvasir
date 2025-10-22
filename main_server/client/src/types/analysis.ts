import { UUID } from "crypto";

export interface AnalysisStatusMessage {
    id: UUID;
    runId: UUID;
    result: AnalysisResult;
    createdAt: string;
}

export interface AnalysisResult {
    id: UUID;
    analysis: string;
    pythonCode: string | null;
    outputVariable: string | null;
    inputVariable: string | null;
    nextType: 'analysis_result' | 'notebook_section' | null;
    nextId: UUID | null;
    sectionId: UUID | null;
}

export interface NotebookSection {
    id: UUID;
    notebookId: UUID;
    sectionName: string;
    sectionDescription?: string;
    nextType: 'analysis_result' | 'notebook_section' | null;
    nextId: UUID | null;
    parentSectionId: UUID | null;
    notebookSections: NotebookSection[];
    analysisResults: AnalysisResult[];
}

export interface Notebook {
    id: UUID;
    notebookSections: NotebookSection[];
}

export interface AnalysisObjectInputEntities {
    datasetIds: UUID[];
    dataSourceIds: UUID[];
    modelEntityIds: UUID[];
}

export interface AnalysisObjectSmall {
    id: UUID;
    name: string;
    description: string | null;
    reportGenerated: boolean;
    createdAt: string;
    inputs: AnalysisObjectInputEntities;
}

export interface AnalysisObject extends AnalysisObjectSmall {
    notebook: Notebook;
}

export interface AnalysisObjectCreate {
    name: string;
    description: string | null;
}

export interface AnalysisRequest {
    projectId: UUID;
    datasetIds: UUID[];
    analysisIds: UUID[];
    automationIds: UUID[];
    prompt: string | null;
    conversationId: UUID;
}

export interface ReportOutlineRequest {
    includeAgentSuggestions: boolean;
    requirements: string | null;
}

export interface NotebookSectionCreate {
    analysisObjectId: UUID;
    sectionName: string;
    sectionDescription: string | null;
    parentSectionId: UUID | null;
}

export interface NotebookSectionUpdate {
    sectionName?: string;
    sectionDescription?: string | null;
}

export interface AnalysisResultUpdate {
    analysis?: string;
}

export interface SectionReorderRequest {
    reorderSections: UUID[];
    precedingSectionId: UUID | null;
    succeedingSectionId: UUID | null;
}

export interface SectionMoveRequest {
    sectionIds: UUID[];
    newParentSectionId: UUID | null;
}

export interface GenerateReportRequest {
    filename: string;
    includeCode: boolean;
}

export interface MoveRequest {
    newSectionId: UUID | null;
    movingElementType: 'analysis_result' | 'notebook_section';
    movingElementId: UUID;
    nextElementType: 'analysis_result' | 'notebook_section' | null;
    nextElementId: UUID | null;
}