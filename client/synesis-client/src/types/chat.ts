
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
}


export type Conversation = {
    id: string;
}

export type ConversationWithMessages = {
    id: string;
    messages: ChatMessage[];
}