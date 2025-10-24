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
    type: "tool_call" | "chat";
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

export type GraphNodeConnections = {
    fromDataSources: UUID[];
    fromDatasets: UUID[];
    fromAnalyses: UUID[];
    fromPipelines: UUID[];
    fromModelEntities: UUID[];
    toDataSources: UUID[];
    toDatasets: UUID[];
    toAnalyses: UUID[];
    toPipelines: UUID[];
    toModelEntities: UUID[];
}

export type DataSourceInGraph = {
    id: UUID;
    name: string;
    type: string;
    briefDescription: string;
    xPosition: number;
    yPosition: number;
    connections: GraphNodeConnections;
}

export type DatasetInGraph = {
    id: UUID;
    name: string;
    briefDescription: string;
    xPosition: number;
    yPosition: number;
    connections: GraphNodeConnections;
}

export type PipelineInGraph = {
    id: UUID;
    name: string;
    briefDescription: string;
    xPosition: number;
    yPosition: number;
    connections: GraphNodeConnections;
}

export type AnalysisInGraph = {
    id: UUID;
    name: string;
    briefDescription: string;
    xPosition: number;
    yPosition: number;
    connections: GraphNodeConnections;
}

export type ModelEntityInGraph = {
    id: UUID;
    name: string;
    briefDescription: string;
    xPosition: number;
    yPosition: number;
    connections: GraphNodeConnections;
}

export type ProjectGraph = {
    dataSources: DataSourceInGraph[];
    datasets: DatasetInGraph[];
    pipelines: PipelineInGraph[];
    analyses: AnalysisInGraph[];
    modelEntities: ModelEntityInGraph[];
}