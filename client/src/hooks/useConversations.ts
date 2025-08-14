import { useSession } from "next-auth/react";
import useSWR from "swr";
import { ConversationCreate, Conversation } from "@/types/orchestrator";
import useSWRMutation from "swr/mutation";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function postConversation(token: string, conversationData: ConversationCreate): Promise<Conversation> {
  const response = await fetch(`${API_URL}/orchestrator/conversation`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(conversationData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create conversation', errorText);
    throw new Error(`Failed to create conversation: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

async function fetchConversations(token: string): Promise<Conversation[]> {
  const response = await fetch(`${API_URL}/orchestrator/conversations`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to get conversations', errorText);
    throw new Error(`Failed to get conversations: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export const useConversations = () => {
  const { data: session } = useSession();
  const { data: conversations, mutate: mutateConversations, error, isLoading } = useSWR(
    session ? ["conversations"] : null, () => fetchConversations(session ? session.APIToken.accessToken : ""));

  const { trigger: createConversation } = useSWRMutation(
    session ? "conversations" : null, 
    async (_, { arg }: { arg: ConversationCreate }) => {
      if (!session) throw new Error("No session");
      
      const newConversation = await postConversation(session.APIToken.accessToken, arg);
      return newConversation;
    },
    {
      populateCache: (newConversation) => {
          return [...(conversations || []), newConversation];
      }
    }
  );

  return {
    conversations,
    mutateConversations,
    isLoading,
    isError: error,
    createConversation,
  };
}; 
