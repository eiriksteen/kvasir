import { postChatContextUpdate } from "@/lib/api";
import { Automation } from "@/types/automations";
import { TimeSeriesDataset } from "@/types/datasets";
import { useSession } from "next-auth/react";
import { useConversation } from "@/hooks/useConversation";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { AnalysisJobResultMetadata } from "@/types/analysis";

export const useContext = () => {
  const { data: session } = useSession();
  const { currentConversationID } = useConversation();
  
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: [] });
  console.log("datasetsInContext", datasetsInContext);
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: [] });
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
        [],
        [],
        true
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
        [arg.id],
        []
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
        [arg.id],
        [],
        true
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

  const { trigger: addAnalysisToContext } = useSWRMutation("analysisesInContext",
    async (_, { arg }: { arg: AnalysisJobResultMetadata }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [],
        [arg.jobId]
      );
      return arg;
    },
    {
      populateCache: (newData: AnalysisJobResultMetadata) => {
        if (analysisesInContext) {
          return [...analysisesInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeAnalysisFromContext } = useSWRMutation("analysisesInContext",
    async (_, { arg }: { arg: AnalysisJobResultMetadata }) => {
      await postChatContextUpdate(
        session?.APIToken.accessToken || "",
        currentConversationID || "",
        [],
        [],
        [arg.jobId],
        true
      );
      return arg;
    },
    {
      populateCache: (newData: AnalysisJobResultMetadata) => {
        if (analysisesInContext) {
          return analysisesInContext.filter((a: AnalysisJobResultMetadata) => a.jobId !== newData.jobId);
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