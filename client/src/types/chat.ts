
export type ChatMessage = {
    role: "user" | "agent";
    type: "tool_call" | "result" | "error" | "chat";
    jobId: string | null;
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
    projectId: string;
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