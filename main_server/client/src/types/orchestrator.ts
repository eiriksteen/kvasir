import { UUID } from "crypto";

export type Context = {
    dataSourceIds: UUID[];
    datasetIds: UUID[];
    pipelineIds: UUID[];
    analysisIds: UUID[];
    modelEntityIds: UUID[];
}

export type ChatMessage = {
    id: UUID;
    role: "user" | "assistant";
    conversationId: UUID;
    context: Context | null;
    content: string;
    createdAt: string;
}

export interface Conversation {
    id: UUID;
    name: string;
    projectId: UUID;
    createdAt: string;
    runIds: UUID[];
}

export type Prompt = {
    conversationId: UUID;
    context: Context | null;
    content: string;
    saveToDb: boolean;
}


export type ConversationCreate = {
    projectId: UUID;
}

export type DataSourceInGraph = {
    id: UUID;
    name: string;
    brief_description: string;
    toDatasets: UUID[];
    toAnalyses: UUID[];
}

export type DatasetInGraph = {
    id: UUID;
    name: string;
    brief_description: string;
    toPipelines: UUID[];
    toAnalyses: UUID[];
}

export type PipelineInGraph = {
    id: UUID;
    name: string;
    brief_description: string;
    fromDatasets: UUID[];
    fromModelEntities: UUID[];
    toDatasets: UUID[];
    toModelEntities: UUID[];
}

export type AnalysisInGraph = {
    id: UUID;
    name: string;
    brief_description: string;
    fromDatasets: UUID[];
    fromDataSources: UUID[];
}

export type ModelEntityInGraph = {
    id: UUID;
    name: string;
    brief_description: string;
    toPipelines: UUID[];
}

export type ProjectGraph = {
    dataSources: DataSourceInGraph[];
    datasets: DatasetInGraph[];
    pipelines: PipelineInGraph[];
    analyses: AnalysisInGraph[];
    modelEntities: ModelEntityInGraph[];
}