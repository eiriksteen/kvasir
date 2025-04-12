import { postConversation, fetchConversations } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'


export const useConversation = () => {
  const { data: session } = useSession();
  const { data: conversations, error, isLoading, mutate: mutateConversations } = useSWR(session ? "conversations" : null, () => fetchConversations(session ? session.APIToken.accessToken : ""));
  const { data: currentConversationID } = useSWR("currentConversation", {fallbackData: null});

  const { trigger: createConversation } = useSWRMutation("currentConversation", () => postConversation(session ? session.APIToken.accessToken : ""), {
    populateCache: (newData) => {
      if (conversations) {
        mutateConversations([...conversations, newData]);
      }
      else{
        mutateConversations([newData]);
      }
      return newData.id;
    }
  });

  return {
    currentConversationID,
    conversations,
    error,
    isLoading,
    createConversation,
  };
}