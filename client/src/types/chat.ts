import { UUID } from "crypto";

export type ChatMessage = {
    id: UUID;
    role: "user" | "agent";
    type: "tool_call" | "result" | "error" | "chat";
    jobId: UUID | null;
    conversationId: UUID;
    content: string;
    context: Context | null;
    createdAt: string;
}

export type Conversation = {
    id: UUID;
    name: string;
    projectId: UUID;
    createdAt: string;
    mode: "chat" | "data_integration" | "analysis" | "automation";
}

export type ConversationWithMessages = {
    id: UUID;
    name: string;
    projectId: UUID;
    messages: ChatMessage[];
    mode: "chat" | "data_integration" | "analysis" | "automation";
    createdAt: string;
}

export type ConversationCreate = {
    projectId: UUID;
    content: string;
}

export type Context = {
    dataSourceIds: UUID[];
    datasetIds: UUID[];
    automationIds: UUID[];
    analysisIds: UUID[];
}

export type Prompt = {
    messageId: UUID;
    conversationId: UUID;
    context: Context | null;
    content: string;
}