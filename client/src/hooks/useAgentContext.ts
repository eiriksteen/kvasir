import { postChatContextUpdate } from "@/lib/api";
import { Automation } from "@/types/automations";
import { Datasets, TimeSeriesDataset } from "@/types/datasets";
import { useSession } from "next-auth/react";
import { useConversation } from "@/hooks/useConversation";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { Analysis } from "@/types/analysis";

const emptyDatasetsInContext: Datasets = {
  timeSeries: [],
}

const emptyAutomationsInContext = {}

export const useAgentContext = () => {
  const { data: session } = useSession();
  const { currentConversationID } = useConversation();
  
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: emptyDatasetsInContext });
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: emptyAutomationsInContext });
  const { data: analysisesInContext } = useSWR("analysisesInContext", { fallbackData: [] });

  const { trigger: addDatasetToContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [arg.id],
        [],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: TimeSeriesDataset) => ({...datasetsInContext, timeSeries: [...datasetsInContext.timeSeries, newData]})
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [arg.id],
        [],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: TimeSeriesDataset) => {
        if (datasetsInContext) {
          return {
            ...datasetsInContext,
            timeSeries: datasetsInContext.timeSeries.filter((d: TimeSeriesDataset) => d.id !== newData.id)
          };
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
        [arg.id],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: Automation) => ({...automationsInContext, [newData.id]: newData})
    }
  );

  const { trigger: removeAutomationFromContext } = useSWRMutation("automationsInContext",
    async (_, { arg }: { arg: Automation }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [arg.id],
        []
      );
      return arg;
    },
    {
      populateCache: (newData: Automation) => {
        if (automationsInContext) {
          return {
            ...automationsInContext,
            [newData.id]: undefined
          };
        }
        return [];
      }
    }
  );

  const { trigger: addAnalysisToContext } = useSWRMutation("analysisesInContext",
    async (_, { arg }: { arg: Analysis }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [],
        [arg.id]
      );
      return arg;
    },
    {
      populateCache: (newData: Analysis) => {
        if (analysisesInContext) {
          return [...analysisesInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeAnalysisFromContext } = useSWRMutation("analysisesInContext",
    async (_, { arg }: { arg: Analysis }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [],
        [arg.id]
      );
      return arg;
    },
    {
      populateCache: (newData: Analysis) => {
        if (analysisesInContext) {
          return analysisesInContext.filter((a: Analysis) => a.id !== newData.id);
        }
        return [];
      }
    }
  );

  return {
    datasetsInContext,
    automationsInContext,
    analysisesInContext,
    addDatasetToContext,
    removeDatasetFromContext,
    addAutomationToContext,
    removeAutomationFromContext,
    addAnalysisToContext,
    removeAnalysisFromContext
  };
}; 