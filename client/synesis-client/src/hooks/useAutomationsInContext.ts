import { postChatContextUpdate } from "@/lib/api";
import { Automation } from "@/types/automations";
import { useSession } from "next-auth/react";
import { useConversations } from "@/hooks/useConversations";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";


export const useAutomationsInContext = () => {
  const { data: session } = useSession();
  const { currentConversationID } = useConversations();
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: [] });

  const { trigger: addAutomationToContext } = useSWRMutation("automationsInContext",
    async (_, { arg }: { arg: Automation }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [arg.id]
      );
      return arg;
    },
    {
      populateCache: (newData: Automation) => {
        if (automationsInContext) {
          return [...automationsInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeAutomationFromContext } = useSWRMutation("automationsInContext",
    async (_, { arg }: { arg: Automation }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [arg.id]
      );
      return arg;
    },
    {
      populateCache: (newData: Automation) => {
        if (automationsInContext) {
          return automationsInContext.filter((a: Automation) => a.id !== newData.id);
        }
        return [];
      }
    }
  );

  return {
    automationsInContext,
    addAutomationToContext,
    removeAutomationFromContext
  };
}; 