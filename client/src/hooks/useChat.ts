import { streamChat, fetchConversations, postConversation } from "@/lib/api";
import { ChatMessage, Prompt, Conversation, Context, ConversationCreate } from "@/types/chat";
import { useCallback } from "react";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation';
import { useAgentContext } from './useAgentContext';
import { useProject } from './useProject';
import { Dataset } from '@/types/data-objects';
import { AnalysisJobResultMetadata } from '@/types/analysis';

export const useChat = (projectId: string) => {
  const {data: session} = useSession();
  const { datasetsInContext, analysisesInContext } = useAgentContext();
  const { selectedProject } = useProject(projectId);

  // Fetch conversations using SWR
  const { data: conversations, error: conversationsError, mutate: mutateConversations } = useSWR(
    session ? ['conversations', session.APIToken.accessToken] : null,
    () => fetchConversations(session!.APIToken.accessToken),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  const { data: currentConversation, mutate: mutateCurrentConversation } = useSWR("currentConversation", {fallbackData: null});

  // Create conversation functionality (moved from useConversation)
  const { trigger: createConversation } = useSWRMutation(
    "currentConversation", 
    async (_, { arg }: { arg: ConversationCreate }) => {
      if (!session) throw new Error("No session");
      
      const newConversation = await postConversation(session.APIToken.accessToken, arg);
      return newConversation;
    },
    {
      populateCache: (newConversation) => {
        if (conversations) {
          mutateConversations([...conversations, { id: newConversation.id, name: newConversation.name, projectId: selectedProject?.id || "", messages: [], createdAt: newConversation.createdAt }]);
        }
        else{
          mutateConversations([{ id: newConversation.id, name: newConversation.name, projectId: selectedProject?.id || "", messages: [], createdAt: newConversation.createdAt }]);
        }
        return newConversation;
      }
    }
  );

  // Function to switch to a different conversation
  const switchConversation = useCallback(async (conversationId: string) => {
    await mutateCurrentConversation(conversations?.find(c => c.id === conversationId));
  }, [mutateCurrentConversation, conversations]);

  // Function to start a new conversation
  const startNewConversation = useCallback(async () => {
    await mutateCurrentConversation(null);
  }, [mutateCurrentConversation]);

  const submitPrompt = useCallback(async (content: string) => {
    if (session) {
      if (content === "") {
        return;
      }

      let conversationId = currentConversation?.id;

      // Create a new conversation if none exists
      if (!conversationId) {
        try {
          const conversationCreateObject: ConversationCreate = {
            projectId: selectedProject?.id || "",
            content: content
          };
          const conversation = await createConversation(conversationCreateObject);
          await mutateCurrentConversation(conversation);
          conversationId = conversation.id;

        } catch (error) {
          console.error('Failed to create conversation:', error);
          return;
        }
      }

      // Create the context with the context data from hooks
      const context: Context = {
        projectId: selectedProject?.id || "",
        datasetIds: datasetsInContext.timeSeries.map((dataset: Dataset) => dataset.id),
        automationIds: [],
        analysisIds: analysisesInContext.map((analysis: AnalysisJobResultMetadata) => analysis.jobId),
      };

      // Create the prompt with conversation_id
      const prompt: Prompt = {
        conversationId: conversationId,
        context: context,
        content: content
      };

      // Create user message with proper context
      const userMessage: ChatMessage = {
        role: "user", 
        conversationId: conversationId,
        content: content,
        context: context,
        createdAt: new Date().toISOString(),
        type: "chat",
        jobId: null
      };
      
      mutateCurrentConversation((prev: Conversation) => ({
        ...prev,
        messages: [...prev.messages, userMessage]
      }));
      
      
      const stream = streamChat(session.APIToken.accessToken, prompt);
      let chunkNum = 0;
      for await (const chunk of stream) {
        if (chunkNum === 0) {
          // Create assistant message with proper context
          const assistantMessage: ChatMessage = {
            conversationId: conversationId,
            role: "agent", 
            content: chunk,
            context: null,
            createdAt: new Date().toISOString(),
            type: "chat",
            jobId: null
          };
          mutateCurrentConversation((prev: Conversation) => ({
            ...prev,
            messages: [...prev.messages, assistantMessage]
          }));
        }
        else {
          mutateCurrentConversation((prev: Conversation) => ({
            ...prev,
            messages: prev.messages.map((msg, i) => 
              i === prev.messages.length - 1 
                ? { ...msg, content: chunk }
                : msg
            )
          }));
        }
        chunkNum++;
      }
    }
  }, [session, createConversation, selectedProject, datasetsInContext, analysisesInContext, currentConversation?.id, mutateCurrentConversation]);

  return { 
    currentConversation, 
    submitPrompt, 
    conversations: conversations || [], 
    conversationsError, 
    mutateConversations,
    isLoadingConversations: !conversations && !conversationsError,
    createConversation,
    switchConversation,
    startNewConversation,
  };
}; 