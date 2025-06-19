export type ChatMessageAPI = {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    conversationId: string;
}

export type ChatMessage = {
    role: "user" | "assistant";
    conversationId: string;
    content: string;
    context: Context | null;
    createdAt: string;
}

export type Conversation = {
    id: string;
    name: string;
    projectId: string;
    messages: ChatMessage[];
    createdAt: string;
}

export type ConversationCreate = {
    project_id: string;
    content: string;
}

export type Context = {
    projectId: string;
    datasetIds: string[];
    automationIds: string[];
    analysisIds: string[];
}

export type Prompt = {
    conversationId: string;
    context: Context | null;
    content: string;
}