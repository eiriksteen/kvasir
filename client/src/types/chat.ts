export type ChatMessageAPI = {
    id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    conversationId: string;
}

export type ChatMessage = {
    role: "user" | "assistant";
    content: string;
    context: Context | null;
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
    prompt: Prompt;
}

export type Context = {
    projectId: string;
    conversationId: string;
    datasetIds: string[];
    automationIds: string[];
    analysisIds: string[];
}

export type Prompt = {
    context: Context | null;
    content: string;
}