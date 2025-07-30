import useSWR from "swr";
import { fetchConversationWithMessages } from "@/lib/api";
import { ChatMessage, Prompt, ConversationWithMessages, Context } from "@/types/chat";
import { useCallback } from "react";
import { useSession } from "next-auth/react";
import { useAgentContext } from './useAgentContext';
import { Dataset } from '@/types/data-objects';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { v4 as uuidv4 } from 'uuid';
import { UUID } from "crypto";
import { DataSource } from "@/types/data-integration";
import { useConversations } from "./useConversations";
import { createChatEventSource } from "@/lib/api";


function createPreliminaryConversation(projectId: UUID, content: string) {

  const conversation: ConversationWithMessages = {
    id: uuidv4() as UUID,
    name: "New Conversation",
    createdAt: new Date().toISOString(),
    mode: "chat",
    projectId: projectId,
    messages: [],
  }

  const userMessage: ChatMessage = {
    id: uuidv4() as UUID,
    role: "user",
    conversationId: conversation.id,
    content: content,
    context: null,
    createdAt: new Date().toISOString(),
    type: "chat",
    jobId: null
  }

  conversation.messages.push(userMessage);

  return conversation;
}


export const useChat = (projectId: UUID) => {
  const { data: session } = useSession();
  const { createConversation } = useConversations();
  const { dataSourcesInContext, datasetsInContext, analysesInContext } = useAgentContext();
  const { data: conversation, error, isLoading, mutate: mutateConversation } = useSWR(`conversation-${projectId}`);

  const setConversationId = useCallback(async (convId: UUID | null) => {
    if (convId) {
      const newConversation = await fetchConversationWithMessages(session ? session.APIToken.accessToken : "", convId);
      mutateConversation(newConversation, {revalidate: false});
    }
    else {
      mutateConversation(undefined, {revalidate: false});
    }
  }, [session, mutateConversation]);

  const submitPrompt = useCallback(async (content: string) => {
    let convId = conversation?.id;
    const isNewConversation = !convId;

    if (isNewConversation) {
      // Ensures immediate UI update
      const preliminaryConversation = createPreliminaryConversation(projectId, content);
      mutateConversation(preliminaryConversation, {revalidate: false});

      const newConversation = await createConversation({ projectId: projectId, content: content });
      await setConversationId(newConversation.id);
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
        analysisIds: analysesInContext?.map((analysis: AnalysisJobResultMetadata) => analysis.jobId) || [],
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
        projectId: projectId,
        context: context,
        content: content
      };
      
      mutateConversation((prev: ConversationWithMessages | undefined) => {
        if (!prev) return prev;
        else {
          return {
            ...prev,
            messages: [...prev.messages, userMessage]
          };
        }
      });

      const eventSource = createChatEventSource(session.APIToken.accessToken, prompt);

      eventSource.onmessage = (ev) => {
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
        };
    }
  }, [session, dataSourcesInContext, datasetsInContext, analysesInContext, conversation, mutateConversation, setConversationId, createConversation, projectId]);

  return { 
    setConversationId,
    conversation, 
    submitPrompt, 
    isLoading,
    isError: error,
  };
}; 