import { postChatContextUpdate } from "@/lib/api";
import { Automation } from "@/types/automations";
import { TimeSeriesDataset } from "@/types/datasets";
import { useSession } from "next-auth/react";
import { useConversation } from "@/hooks/useConversation";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";

export const useContext = () => {
  const { data: session } = useSession();
  const { currentConversationID } = useConversation();
  
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: [] });
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: [] });

  const { trigger: addDatasetToContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [arg.id],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: TimeSeriesDataset) => {
        if (datasetsInContext) {
          return [...datasetsInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [arg.id],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: TimeSeriesDataset) => {
        if (datasetsInContext) {
          return datasetsInContext.filter((d: TimeSeriesDataset) => d.id !== newData.id);
        }
        return [];
      }
    }
  );

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
    datasetsInContext,
    automationsInContext,
    addDatasetToContext,
    removeDatasetFromContext,
    addAutomationToContext,
    removeAutomationFromContext
  };
}; 