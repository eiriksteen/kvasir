import { useSession } from "next-auth/react";
import useSWR from "swr";
import { fetchConversations, postConversation } from "@/lib/api";
import { ConversationCreate } from "@/types/orchestrator";
import useSWRMutation from "swr/mutation";

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
