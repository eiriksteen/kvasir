import { streamChat, fetchMessages, fetchConversations, postConversation } from "@/lib/api";
import { ChatMessage, Prompt, Conversation, Context } from "@/types/chat";
import { useEffect, useState, useCallback } from "react";
import { apiMessageToChatMessage } from "@/lib/utils";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation';
import { useAgentContext } from './useAgentContext';
import { useProject } from './useProject';
import { TimeSeriesDataset } from '@/types/datasets';
import { AnalysisJobResultMetadata } from '@/types/analysis';

export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const {data: session} = useSession();
  const { datasetsInContext, analysisesInContext } = useAgentContext();
  const { selectedProject } = useProject();

  // Fetch conversations using SWR
  const { data: conversations, error: conversationsError, mutate: mutateConversations } = useSWR(
    session ? ['conversations', session.APIToken.accessToken] : null,
    () => fetchConversations(session!.APIToken.accessToken),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  // Current conversation ID management (moved from useConversation)
  const { data: currentConversationID, mutate: mutateCurrentConversationID } = useSWR("currentConversation", {fallbackData: null});

  // Create conversation functionality (moved from useConversation)
  const { trigger: createConversation } = useSWRMutation(
    "currentConversation", 
    async () => {
      if (!session) throw new Error("No session");
      
      // Create a default prompt without context for new conversation
      const defaultPrompt: Prompt = {
        context: null, // No context for new conversation
        content: ""
      };

      const newConversation = await postConversation(session.APIToken.accessToken, {
        project_id: selectedProject?.id || "",
        prompt: defaultPrompt
      });
      return newConversation.id;
    },
    {
      populateCache: (newConversationId) => {
        if (conversations) {
          mutateConversations([...conversations, { id: newConversationId, name: "New Conversation", projectId: selectedProject?.id || "", messages: [], createdAt: new Date().toISOString() }]);
        }
        else{
          mutateConversations([{ id: newConversationId, name: "New Conversation", projectId: selectedProject?.id || "", messages: [], createdAt: new Date().toISOString() }]);
        }
        return newConversationId;
      }
    }
  );

  // Function to switch to a different conversation
  const switchConversation = useCallback(async (conversationId: string) => {
    if (session) {
      // Update the current conversation ID
      await mutateCurrentConversationID(conversationId);
      
      // Fetch messages for the new conversation
      try {
        const fetchedMessages = await fetchMessages(session.APIToken.accessToken, conversationId);
        setMessages(fetchedMessages.map(apiMessageToChatMessage));
      } catch (error) {
        console.error('Failed to fetch messages for conversation:', error);
        setMessages([]);
      }
    }
  }, [session, mutateCurrentConversationID]);

  useEffect(() => {
    if (session) {
      if (currentConversationID) {
        fetchMessages(session.APIToken.accessToken, currentConversationID).then((fetchedMessages) => {
          setMessages(fetchedMessages.map(apiMessageToChatMessage));
        });
      }
    }
  }, [currentConversationID, session]);

  const submitPrompt = useCallback(async (content: string) => {
    if (session) {
      if (content === "") {
        return;
      }

      let conversationId = currentConversationID;
      
      // Create a new conversation if none exists
      if (!conversationId) {
        try {
          conversationId = await createConversation();
        } catch (error) {
          console.error('Failed to create conversation:', error);
          return;
        }
      }

      // Create the context with the conversation ID and context data from hooks
      const context: Context = {
        projectId: selectedProject?.id || "",
        conversationId: conversationId,
        datasetIds: datasetsInContext.timeSeries.map((dataset: TimeSeriesDataset) => dataset.id),
        automationIds: [],
        analysisIds: analysisesInContext.map((analysis: AnalysisJobResultMetadata) => analysis.jobId),
      };

      // Create the prompt
      const prompt: Prompt = {
        context,
        content
      };

      // Create user message with proper context
      const userMessage: ChatMessage = {
        role: "user", 
        content: content,
        context: context
      };
      
      setMessages(prevMessages => [...prevMessages, userMessage]);
      
      const stream = streamChat(session.APIToken.accessToken, prompt);
      let chunkNum = 0;
      for await (const chunk of stream) {
        if (chunkNum === 0) {
          // Create assistant message with proper context
          const assistantMessage: ChatMessage = {
            role: "assistant", 
            content: chunk,
            context: context
          };
          setMessages(prevMessages => [...prevMessages, assistantMessage]);
        }
        else {
          setMessages(prevMessages => {
            const updatedMessages = [...prevMessages];
            updatedMessages[updatedMessages.length - 1] = {
              role: "assistant", 
              content: chunk,
              context: context
            };
            return updatedMessages;
          });
        }
        chunkNum++;
      }
    }
  }, [session, currentConversationID, createConversation, selectedProject, datasetsInContext, analysisesInContext]);

  return { 
    messages, 
    submitPrompt, 
    conversations: conversations || [], 
    conversationsError, 
    mutateConversations,
    isLoadingConversations: !conversations && !conversationsError,
    currentConversationID,
    createConversation,
    switchConversation,
  };
}; 