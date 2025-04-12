import { postChatContextUpdate } from "@/lib/api";
import { TimeSeriesDataset } from "@/types/datasets";
import { useSession } from "next-auth/react";
import { useConversations } from "@/hooks/useConversations";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";


export const useDatasetsInContext = () => {
  const { data: session } = useSession();
  const { currentConversationID } = useConversations();
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: [] });

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

  return {
    datasetsInContext,
    addDatasetToContext,
    removeDatasetFromContext
  };
};