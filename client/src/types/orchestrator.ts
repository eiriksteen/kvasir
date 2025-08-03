import { UUID } from "crypto";

export type Context = {
    dataSourceIds: UUID[];
    datasetIds: UUID[];
    automationIds: UUID[];
    analysisIds: UUID[];
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
    conversationId: UUID | null;
    projectId: UUID | null;
    context: Context | null;
    content: string;
}


export type ConversationCreate = {
    projectId: UUID;
}