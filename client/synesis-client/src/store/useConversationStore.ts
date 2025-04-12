import { create } from "zustand";

interface ConversationStore {
  currentConversationId: string | null;
  conversationIds: string[];
  setCurrentConversationId: (conversationId: string | null) => void;
  setConversationIds: (conversationIds: string[]) => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  currentConversationId: null,
  conversationIds: [],
  setCurrentConversationId: (conversationId) => set(() => ({ currentConversationId: conversationId })),
  setConversationIds: (conversationIds) => set(() => ({ conversationIds: conversationIds })),
})); 