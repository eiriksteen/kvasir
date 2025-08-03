import { Automation } from "@/types/automation";
import { Dataset } from "@/types/data-objects";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { AnalysisJobResultMetadata } from "@/types/analysis";
import { DataSource } from "@/types/data-integration";


// Do this to avoid "possibly undefined" type errors
const emptyDataSourcesInContext: DataSource[] = [];
const emptyDatasetsInContext: Dataset[] = [];
const emptyAutomationsInContext: Automation[] = [];
const emptyAnalysisesInContext: AnalysisJobResultMetadata[] = [];


export const useAgentContext = () => {
  
  const { data: dataSourcesInContext } = useSWR("dataSourcesInContext", { fallbackData: emptyDataSourcesInContext });
  const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: emptyDatasetsInContext });
  const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: emptyAutomationsInContext });
  const { data: analysesInContext } = useSWR("analysisesInContext", { fallbackData: emptyAnalysisesInContext });


  const { trigger: addDataSourceToContext } = useSWRMutation("dataSourcesInContext",
    async (_, { arg }: { arg: DataSource }) => {
      return arg;
    },
    {
      populateCache: (newData: DataSource) => ([...(dataSourcesInContext || []), newData])
    }
  );

  const { trigger: removeDataSourceFromContext } = useSWRMutation("dataSourcesInContext",
    async (_, { arg }: { arg: DataSource }) => {
      return arg;
    },
    {
      populateCache: (newData: DataSource) => {
        if (dataSourcesInContext) {
          return dataSourcesInContext.filter((d: DataSource) => d.id !== newData.id);
        }
        return [];
      }
    }
  );

  const { trigger: addDatasetToContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: Dataset }) => {
      return arg;
    },
    {
      populateCache: (newData: Dataset) => ([...(datasetsInContext || []), newData])
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation("datasetsInContext",
    async (_, { arg }: { arg: Dataset }) => {
      return arg;
    },
    {
      populateCache: (newData: Dataset) => {
        if (datasetsInContext) {
          return datasetsInContext.filter((d: Dataset) => d.id !== newData.id);
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
      populateCache: (newData: Automation) => ([...(automationsInContext || []), newData])
    }
  );

  const { trigger: removeAutomationFromContext } = useSWRMutation("automationsInContext",
    async (_, { arg }: { arg: Automation }) => {
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
      return arg;
    },
    {
      populateCache: (newData: AnalysisJobResultMetadata) => {
        if (analysesInContext) {
          return [...analysesInContext, newData];
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
        if (analysesInContext) {
          return analysesInContext.filter((a: AnalysisJobResultMetadata) => a.jobId !== newData.jobId);
        }
        return [];
      }
    }
  );


  return {
    dataSourcesInContext,
    datasetsInContext,
    automationsInContext,
    analysesInContext,
    addDataSourceToContext,
    removeDataSourceFromContext,
    addDatasetToContext,
    removeDatasetFromContext,
    addAutomationToContext,
    removeAutomationFromContext,
    addAnalysisToContext,
    removeAnalysisFromContext
  };
}; 