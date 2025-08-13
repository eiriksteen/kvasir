import useSWR from "swr";
import { fetchConversationMessages } from "@/lib/api";
import { ChatMessage, Prompt, Context } from "@/types/orchestrator";
import { useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import { useAgentContext } from './useAgentContext';
import { Dataset } from '@/types/data-objects';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { v4 as uuidv4 } from 'uuid';
import { UUID } from "crypto";
import { DataSource } from "@/types/data-sources";
import { useConversations } from "./useConversations";
import { createOrchestratorEventSource } from "@/lib/api";


export const useConversationMessages = (conversationId: UUID | null) => {
  const { data: session } = useSession();

  // Should optimize to just refetch conversations affected by runs in progress
  const { data: conversationMessages, mutate: mutateConversationMessages, error, isLoading } = useSWR<ChatMessage[]>(
   session ? ["conversationMessages", conversationId] : null, 
   async () => {
    if (conversationId) {
      return await fetchConversationMessages(session ? session.APIToken.accessToken : "", conversationId) as ChatMessage[];
    }
    else {
      return []
    }
  }
  );

  return {
    conversationMessages: conversationMessages || [],
    error,
    isLoading,
    mutateConversationMessages
  }
}


export const useProjectChat = (projectId: UUID) => {
  const { data: session } = useSession();
  const { conversations, createConversation, mutateConversations } = useConversations();
  const { dataSourcesInContext, datasetsInContext, analysesInContext } = useAgentContext();

  const { data: projectConversationId, mutate: setProjectConversationId } = useSWR(
    session ? ["project-conversation-id", projectId] : null, {fallbackData: null}
  );
  const { conversationMessages, error, isLoading, mutateConversationMessages } = useConversationMessages(projectConversationId);

  const conversation = useMemo(() => {
    return conversations?.find(conv => conv.id === projectConversationId) || null;
  }, [conversations, projectConversationId]);


  const submitPrompt = useCallback(async (content: string) => {
    if (session) {
      if (content === "") {
        return;
      }

      const isNewConversation = !projectConversationId;
      let convId = projectConversationId;

      if (isNewConversation) {
        const newConversation = await createConversation({projectId: projectId});
        convId = newConversation.id;
        await setProjectConversationId(newConversation.id, {revalidate: false});
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
      };

      // Create the prompt with conversation_id
      const prompt: Prompt = {
        conversationId: convId,
        context: context,
        content: content
      };

      mutateConversationMessages([...conversationMessages, userMessage], {revalidate: false});

      const eventSource = createOrchestratorEventSource(session.APIToken.accessToken, prompt);

      eventSource.onmessage = (ev) => {
          const data: ChatMessage = JSON.parse(ev.data);

          if (data.content === "DONE") {
            if (isNewConversation) {
              mutateConversations();
            }
          }
          else {
            mutateConversationMessages((prev: ChatMessage[] | undefined) => {
              if (!prev) return prev;
              // If message with the same id already exists, update it, else add it
              const existingMessage = prev.find((msg) => msg.id === data.id);
              if (existingMessage) {
                return prev.map((msg) => msg.id === data.id ? data : msg)
              }
              else {
                return [...prev, data]
              }
            }, {revalidate: false});
        }
      };
    }
  }, [
    session, 
    dataSourcesInContext, 
    datasetsInContext, 
    analysesInContext, 
    conversationMessages, 
    projectConversationId, 
    projectId,
    setProjectConversationId,
    mutateConversations,
    createConversation,
    mutateConversationMessages
  ]);

  return { 
    conversation,
    conversationMessages, 
    submitPrompt, 
    isLoading,
    isError: error,
    setProjectConversationId,
  };
}; 