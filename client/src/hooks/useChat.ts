import useSWR from "swr";
import { fetchConversationWithMessages } from "@/lib/api";
import { ChatMessage, Prompt, ConversationWithMessages, Context } from "@/types/chat";
import { useCallback } from "react";
import { useSession } from "next-auth/react";
import { useAgentContext } from './useAgentContext';
import { Dataset } from '@/types/data-objects';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { v4 as uuidv4 } from 'uuid';
import { UUID } from "crypto";
import { DataSource } from "@/types/data-integration";
import { useConversations } from "./useConversations";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export const useChat = (projectId: UUID) => {
  const { data: session } = useSession();
  const { createConversation } = useConversations();
  const { dataSourcesInContext, datasetsInContext, analysisesInContext } = useAgentContext();
  const { data: conversationId, mutate: setConversationId } = useSWR("conversationId", { fallbackData: null });

  const { data: conversation, error, isLoading, mutate: mutateConversation } = useSWR(
    session && conversationId ? `conversation-${conversationId}` : null, 
    () => fetchConversationWithMessages(session ? session.APIToken.accessToken : "", conversationId),
  );

  const submitPrompt = useCallback(async (content: string) => {
    let convId = conversationId;

    if (!convId) {
      const newConversation = await createConversation({ projectId: projectId, content: content });
      setConversationId(newConversation.id);
      convId = newConversation.id;
    }

    if (session) {
      if (content === "") {
        return;
      }

      // Create the context with the context data from hooks
      const context: Context = {
        dataSourceIds: dataSourcesInContext?.map((dataSource: DataSource) => dataSource.id) || [],
        datasetIds: datasetsInContext?.map((dataset: Dataset) => dataset.id) || [],
        automationIds: [],
        analysisIds: analysisesInContext?.map((analysis: AnalysisJobResultMetadata) => analysis.jobId) || [],
      };

      // Create user message with proper context
      const userMessage: ChatMessage = {
        // Placeholder id, the backend will create the actual id
        id: uuidv4() as UUID,
        role: "user", 
        conversationId: convId,
        content: content,
        context: context,
        createdAt: new Date().toISOString(),
        type: "chat",
        jobId: null
      };

      // Create the prompt with conversation_id
      const prompt: Prompt = {
        messageId: userMessage.id,
        conversationId: convId,
        context: context,
        content: content
      };
      
      mutateConversation((prev: ConversationWithMessages | undefined) => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: [...prev.messages, userMessage]
        };
      });

      console.log(JSON.stringify(prompt))

      await fetchEventSource(`${API_URL}/chat/completions`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.APIToken.accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(prompt),
          onmessage(ev) {
              const data: ChatMessage = JSON.parse(ev.data);
              mutateConversation((prev: ConversationWithMessages | undefined) => {
                if (!prev) return prev;
                // If message with the same id already exists, update it, else add it
                const existingMessage = prev.messages.find((msg) => msg.id === data.id);
                if (existingMessage) {
                  return {
                    ...prev,
                    messages: prev.messages.map((msg) => msg.id === data.id ? data : msg)
                  };
                }
                else {
                  return {
                    ...prev,
                    messages: [...prev.messages, data]
                  };
                }
              });
          }

      });
      
    }
  }, [session, dataSourcesInContext, datasetsInContext, analysisesInContext, conversationId, mutateConversation, setConversationId, createConversation, projectId]);

  return { 
    conversationId,
    setConversationId,
    conversation, 
    submitPrompt, 
    isLoading,
    isError: error,
  };
}; 