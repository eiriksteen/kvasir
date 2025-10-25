import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { UUID } from "crypto";


// Do this to avoid "possibly undefined" type errors
const emptyDataSourcesInContext: UUID[] = [];
const emptyDatasetsInContext: UUID[] = [];
const emptyPipelinesInContext: UUID[] = [];
const emptyAnalysisesInContext: UUID[] = [];
const emptyModelEntitiesInContext: UUID[] = [];


export const useAgentContext = (projectId: UUID) => {

  const { data: dataSourcesInContext } = useSWR(["dataSourcesInContext", projectId], { fallbackData: emptyDataSourcesInContext });
  const { data: datasetsInContext } = useSWR(["datasetsInContext", projectId], { fallbackData: emptyDatasetsInContext });
  const { data: pipelinesInContext } = useSWR(["pipelinesInContext", projectId], { fallbackData: emptyPipelinesInContext });
  const { data: analysesInContext } = useSWR(["analysisesInContext", projectId], { fallbackData: emptyAnalysisesInContext });
  const { data: modelEntitiesInContext } = useSWR(["modelEntitiesInContext", projectId], { fallbackData: emptyModelEntitiesInContext });

  const { trigger: addDataSourceToContext } = useSWRMutation(["dataSourcesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => ([...(dataSourcesInContext || []), newData])
    }
  );

  const { trigger: removeDataSourceFromContext } = useSWRMutation(["dataSourcesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (dataSourcesInContext) {
          return dataSourcesInContext.filter((d: UUID) => d !== newData);
        }
        return [];
      }
    }
  );

  const { trigger: addDatasetToContext } = useSWRMutation(["datasetsInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => ([...(datasetsInContext || []), newData])
    }
  );

  const { trigger: removeDatasetFromContext } = useSWRMutation(["datasetsInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (datasetsInContext) {
          return datasetsInContext.filter((d: UUID) => d !== newData);
        }
        return [];
      }
    }
  );

  const { trigger: addPipelineToContext } = useSWRMutation(["pipelinesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => ([...(pipelinesInContext || []), newData])
    }
  );

  const { trigger: removePipelineFromContext } = useSWRMutation(["pipelinesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (pipelinesInContext) {
          return pipelinesInContext.filter((a: UUID) => a !== newData);
        }
        return [];
      }
    }
  );

  const { trigger: addAnalysisToContext } = useSWRMutation(["analysisesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (analysesInContext) {
          return [...analysesInContext, newData];
        }
        return [newData];
      }
    }
  );

  const { trigger: removeAnalysisFromContext } = useSWRMutation(["analysisesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (analysesInContext) {
          return analysesInContext.filter((a: UUID) => a !== newData);
        }
        return [];
      }
    }
  );

  const { trigger: addModelEntityToContext } = useSWRMutation(["modelEntitiesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => ([...(modelEntitiesInContext || []), newData])
    }
  );

  const { trigger: removeModelEntityFromContext } = useSWRMutation(["modelEntitiesInContext", projectId],
    async (_, { arg }: { arg: UUID }) => {
      return arg;
    },
    {
      populateCache: (newData: UUID) => {
        if (modelEntitiesInContext) {
          return modelEntitiesInContext.filter((m: UUID) => m !== newData);
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