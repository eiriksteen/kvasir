import { Automation } from "@/types/automations";
import { Datasets, TimeSeriesDataset } from "@/types/datasets";
import { useSession } from "next-auth/react";
import { useConversation } from "@/hooks/useConversation";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { AnalysisJobResultMetadata } from "@/types/analysis";

const emptyDatasetsInContext: Datasets = {
  timeSeries: [],
}

const emptyAutomationsInContext = {}

export const useAgentContext = () => {
  
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: emptyDatasetsInContext });
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: emptyAutomationsInContext });
  const { data: analysisesInContext } = useSWR("analysisesInContext", { fallbackData: [] });

  const { trigger: addDatasetToContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
      return arg;
    },
    {
      populateCache: (newData: TimeSeriesDataset) => ({...datasetsInContext, timeSeries: [...datasetsInContext.timeSeries, newData]})
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: TimeSeriesDataset }) => {
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
      return arg;
    },
    {
      populateCache: (newData: Automation) => ({...automationsInContext, [newData.id]: newData})
    }
  );

  const { trigger: removeAutomationFromContext } = useSWRMutation("automationsInContext",
    async (_, { arg }: { arg: Automation }) => {
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
    async (_, { arg }: { arg: AnalysisJobResultMetadata }) => {
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