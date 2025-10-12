import { Pipeline } from "@/types/pipeline";
import { Dataset } from "@/types/data-objects";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { AnalysisObjectSmall } from "@/types/analysis";
import { DataSource } from "@/types/data-sources";
import { ModelEntity } from "@/types/model";
import { UUID } from "crypto";


// Do this to avoid "possibly undefined" type errors
const emptyDataSourcesInContext: DataSource[] = [];
const emptyDatasetsInContext: Dataset[] = [];
const emptyPipelinesInContext: Pipeline[] = [];
const emptyAnalysisesInContext: [] = [];
const emptyModelEntitiesInContext: ModelEntity[] = [];


export const useAgentContext = (projectId: UUID) => {

  const { data: dataSourcesInContext } = useSWR(["dataSourcesInContext", projectId], { fallbackData: emptyDataSourcesInContext });
  const { data: datasetsInContext } = useSWR(["datasetsInContext", projectId], { fallbackData: emptyDatasetsInContext });
  const { data: pipelinesInContext } = useSWR(["pipelinesInContext", projectId], { fallbackData: emptyPipelinesInContext });
  const { data: analysesInContext } = useSWR(["analysisesInContext", projectId], { fallbackData: emptyAnalysisesInContext });
  const { data: modelEntitiesInContext } = useSWR(["modelEntitiesInContext", projectId], { fallbackData: emptyModelEntitiesInContext });

  const { trigger: addDataSourceToContext } = useSWRMutation(["dataSourcesInContext", projectId],
    async (_, { arg }: { arg: DataSource }) => {
      return arg;
    },
    {
      populateCache: (newData: DataSource) => ([...(dataSourcesInContext || []), newData])
    }
  );

  const { trigger: removeDataSourceFromContext } = useSWRMutation(["dataSourcesInContext", projectId],
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

  const { trigger: addDatasetToContext } = useSWRMutation(["datasetsInContext", projectId],
    async (_, { arg }: { arg: Dataset }) => {
      return arg;
    },
    {
      populateCache: (newData: Dataset) => ([...(datasetsInContext || []), newData])
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation(["datasetsInContext", projectId],
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

  const { trigger: addPipelineToContext } = useSWRMutation(["pipelinesInContext", projectId],
    async (_, { arg }: { arg: Pipeline }) => {
      return arg;
    },
    {
      populateCache: (newData: Pipeline) => ([...(pipelinesInContext || []), newData])
    }
  );

  const { trigger: removePipelineFromContext } = useSWRMutation(["pipelinesInContext", projectId],
    async (_, { arg }: { arg: Pipeline }) => {
      return arg;
    },
    {
      populateCache: (newData: Pipeline) => {
        if (pipelinesInContext) {
          return pipelinesInContext.filter((a: Pipeline) => a.id !== newData.id);
        }
        return [];
      }
    }
  );

  const { trigger: addAnalysisToContext } = useSWRMutation(["analysisesInContext", projectId],
    async (_, { arg }: { arg: AnalysisObjectSmall }) => {
      return arg;
    },
    {
      populateCache: (newData: AnalysisObjectSmall) => {
        if (analysesInContext) {
          return [...analysesInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeAnalysisFromContext } = useSWRMutation(["analysisesInContext", projectId],
    async (_, { arg }: { arg: AnalysisObjectSmall }) => {
      return arg;
    },
    {
      populateCache: (newData: AnalysisObjectSmall) => {
        if (analysesInContext) {
          return analysesInContext.filter((a: AnalysisObjectSmall) => a.id !== newData.id);
        }
        return [];
      }
    }
  );

  const { trigger: addModelEntityToContext } = useSWRMutation(["modelEntitiesInContext", projectId],
    async (_, { arg }: { arg: ModelEntity }) => {
      return arg;
    },
    {
      populateCache: (newData: ModelEntity) => ([...(modelEntitiesInContext || []), newData])
    }
  );

  const { trigger: removeModelEntityFromContext } = useSWRMutation(["modelEntitiesInContext", projectId],
    async (_, { arg }: { arg: ModelEntity }) => {
      return arg;
    },
    {
      populateCache: (newData: ModelEntity) => {
        if (modelEntitiesInContext) {
          return modelEntitiesInContext.filter((m: ModelEntity) => m.id !== newData.id);
        }
        return [];
      }
    }
  );



  return {
    dataSourcesInContext,
    datasetsInContext,
    pipelinesInContext,
    analysesInContext,
    modelEntitiesInContext,
    addDataSourceToContext,
    removeDataSourceFromContext,
    addDatasetToContext,
    removeDatasetFromContext,
    addPipelineToContext,
    removePipelineFromContext,
    addAnalysisToContext,
    removeAnalysisFromContext,
    addModelEntityToContext,
    removeModelEntityFromContext,
  };
}; 