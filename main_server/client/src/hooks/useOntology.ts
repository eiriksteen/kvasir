import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { DataSource, DataSourceCreate } from "@/types/ontology/data-source";
import { Dataset, DatasetCreate } from "@/types/ontology/dataset";
import { Pipeline, PipelineCreate } from "@/types/ontology/pipeline";
import { ModelInstantiated, ModelInstantiatedCreate } from "@/types/ontology/model";
import { Analysis, AnalysisCreate } from "@/types/ontology/analysis";
import { EntityGraph, EdgeDefinition } from "@/types/ontology/entity-graph";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Fetch mounted data sources
async function fetchMountedDataSources(token: string, mountGroupId: UUID): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/data-sources`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch mounted data sources', errorText);
    throw new Error(`Failed to fetch mounted data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Fetch mounted datasets
async function fetchMountedDatasets(token: string, mountGroupId: UUID): Promise<Dataset[]> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/datasets`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch mounted datasets', errorText);
    throw new Error(`Failed to fetch mounted datasets: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Fetch mounted pipelines
async function fetchMountedPipelines(token: string, mountGroupId: UUID): Promise<Pipeline[]> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/pipelines`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch mounted pipelines', errorText);
    throw new Error(`Failed to fetch mounted pipelines: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Fetch mounted models instantiated
async function fetchMountedModelsInstantiated(token: string, mountGroupId: UUID): Promise<ModelInstantiated[]> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/models-instantiated`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch mounted models instantiated', errorText);
    throw new Error(`Failed to fetch mounted models instantiated: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Fetch mounted analyses
async function fetchMountedAnalyses(token: string, mountGroupId: UUID): Promise<Analysis[]> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/analyses`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch mounted analyses', errorText);
    throw new Error(`Failed to fetch mounted analyses: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Fetch entity graph
async function fetchEntityGraph(token: string, mountGroupId: UUID): Promise<EntityGraph> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/entity-graph`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch entity graph', errorText);
    throw new Error(`Failed to fetch entity graph: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Create entity functions
async function insertDataSource(
  token: string,
  mountGroupId: UUID,
  dataSourceCreate: DataSourceCreate,
  edges: EdgeDefinition[] = []
): Promise<DataSource> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/data-source`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ dataSource: dataSourceCreate, edges }))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert data source: ${response.status} ${errorText}`);
  }

  return snakeToCamelKeys(await response.json());
}

async function insertDataset(
  token: string,
  mountGroupId: UUID,
  datasetCreate: DatasetCreate,
  edges: EdgeDefinition[] = []
): Promise<Dataset> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/dataset`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ dataset: datasetCreate, edges }))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert dataset: ${response.status} ${errorText}`);
  }

  return snakeToCamelKeys(await response.json());
}

async function insertPipeline(
  token: string,
  mountGroupId: UUID,
  pipelineCreate: PipelineCreate,
  edges: EdgeDefinition[] = []
): Promise<Pipeline> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/pipeline`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ pipeline: pipelineCreate, edges }))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert pipeline: ${response.status} ${errorText}`);
  }

  return snakeToCamelKeys(await response.json());
}

async function insertModelInstantiated(
  token: string,
  mountGroupId: UUID,
  modelInstantiatedCreate: ModelInstantiatedCreate,
  edges: EdgeDefinition[] = []
): Promise<ModelInstantiated> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/model-instantiated`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ modelInstantiated: modelInstantiatedCreate, edges }))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert model instantiated: ${response.status} ${errorText}`);
  }

  return snakeToCamelKeys(await response.json());
}

async function insertAnalysis(
  token: string,
  mountGroupId: UUID,
  analysisCreate: AnalysisCreate,
  edges: EdgeDefinition[] = []
): Promise<Analysis> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/analysis`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ analysis: analysisCreate, edges }))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert analysis: ${response.status} ${errorText}`);
  }

  return snakeToCamelKeys(await response.json());
}

async function insertFilesDataSources(
  token: string,
  mountGroupId: UUID,
  files: File[],
  edges: EdgeDefinition[] = []
): Promise<DataSource[]> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('edges', JSON.stringify(camelToSnakeKeys(edges)));

  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/files-data-sources`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to insert files data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Delete entity functions
async function deleteDataSource(token: string, mountGroupId: UUID, dataSourceId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/data-source/${dataSourceId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete data source: ${response.status} ${errorText}`);
  }
}

async function deleteDataset(token: string, mountGroupId: UUID, datasetId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/dataset/${datasetId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete dataset: ${response.status} ${errorText}`);
  }
}

async function deletePipeline(token: string, mountGroupId: UUID, pipelineId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/pipeline/${pipelineId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete pipeline: ${response.status} ${errorText}`);
  }
}

async function deleteModelInstantiated(token: string, mountGroupId: UUID, modelInstantiatedId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/model-instantiated/${modelInstantiatedId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete model instantiated: ${response.status} ${errorText}`);
  }
}

async function deleteAnalysis(token: string, mountGroupId: UUID, analysisId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountGroupId}/analysis/${analysisId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete analysis: ${response.status} ${errorText}`);
  }
}

/**
 * Hook for accessing ontology methods for a specific project (mount group).
 * This mirrors the backend Ontology class and provides convenient access to
 * all entities mounted in a project.
 * 
 * @param mountGroupId - Required UUID of the project/mount group
 */
export const useOntology = (mountGroupId: UUID) => {
  const { data: session } = useSession();

  // Fetch mounted data sources
  const { 
    data: dataSources, 
    mutate: mutateDataSources, 
    error: dataSourcesError, 
    isLoading: dataSourcesLoading 
  } = useSWR(
    session && mountGroupId ? ["data-sources", mountGroupId] : null,
    () => fetchMountedDataSources(session!.APIToken.accessToken, mountGroupId!)
  );

  // Fetch mounted datasets
  const { 
    data: datasets, 
    mutate: mutateDatasets, 
    error: datasetsError, 
    isLoading: datasetsLoading 
  } = useSWR(
    session && mountGroupId ? ["datasets", mountGroupId] : null,
    () => fetchMountedDatasets(session!.APIToken.accessToken, mountGroupId!)
  );

  // Fetch mounted pipelines
  const { 
    data: pipelines, 
    mutate: mutatePipelines, 
    error: pipelinesError, 
    isLoading: pipelinesLoading 
  } = useSWR(
    session && mountGroupId ? ["pipelines", mountGroupId] : null,
    () => fetchMountedPipelines(session!.APIToken.accessToken, mountGroupId!)
  );

  // Fetch mounted models instantiated
  const { 
    data: modelsInstantiated, 
    mutate: mutateModelsInstantiated, 
    error: modelsInstantiatedError, 
    isLoading: modelsInstantiatedLoading 
  } = useSWR(
    session && mountGroupId ? ["models-instantiated", mountGroupId] : null,
    () => fetchMountedModelsInstantiated(session!.APIToken.accessToken, mountGroupId!)
  );

  // Fetch mounted analyses
  const { 
    data: analyses, 
    mutate: mutateAnalyses, 
    error: analysesError, 
    isLoading: analysesLoading 
  } = useSWR(
    session && mountGroupId ? ["analyses", mountGroupId] : null,
    () => fetchMountedAnalyses(session!.APIToken.accessToken, mountGroupId!)
  );

  // Fetch entity graph
  const { 
    data: entityGraph, 
    mutate: mutateEntityGraph, 
    error: entityGraphError, 
    isLoading: entityGraphLoading 
  } = useSWR(
    session && mountGroupId ? ["entity-graph", mountGroupId] : null,
    () => fetchEntityGraph(session!.APIToken.accessToken, mountGroupId!)
  );

  // Mutation hooks for insert operations
  const { trigger: triggerInsertDataSource } = useSWRMutation(
    ["data-sources", mountGroupId],
    async (_, { arg }: { arg: { dataSourceCreate: DataSourceCreate; edges?: EdgeDefinition[] } }) => {
      const newDataSource = await insertDataSource(session!.APIToken.accessToken, mountGroupId, arg.dataSourceCreate, arg.edges || []);
      await mutateDataSources();
      await mutateEntityGraph();
      return newDataSource;
    }
  );

  const { trigger: triggerInsertDataset } = useSWRMutation(
    ["datasets", mountGroupId],
    async (_, { arg }: { arg: { datasetCreate: DatasetCreate; edges?: EdgeDefinition[] } }) => {
      const newDataset = await insertDataset(session!.APIToken.accessToken, mountGroupId, arg.datasetCreate, arg.edges || []);
      await mutateDatasets();
      await mutateEntityGraph();
      return newDataset;
    }
  );

  const { trigger: triggerInsertPipeline } = useSWRMutation(
    ["pipelines", mountGroupId],
    async (_, { arg }: { arg: { pipelineCreate: PipelineCreate; edges?: EdgeDefinition[] } }) => {
      const newPipeline = await insertPipeline(session!.APIToken.accessToken, mountGroupId, arg.pipelineCreate, arg.edges || []);
      await mutatePipelines();
      await mutateEntityGraph();
      return newPipeline;
    }
  );

  const { trigger: triggerInsertModelInstantiated } = useSWRMutation(
    ["models-instantiated", mountGroupId],
    async (_, { arg }: { arg: { modelInstantiatedCreate: ModelInstantiatedCreate; edges?: EdgeDefinition[] } }) => {
      const newModel = await insertModelInstantiated(session!.APIToken.accessToken, mountGroupId, arg.modelInstantiatedCreate, arg.edges || []);
      await mutateModelsInstantiated();
      await mutateEntityGraph();
      return newModel;
    }
  );

  const { trigger: triggerInsertAnalysis } = useSWRMutation(
    ["analyses", mountGroupId],
    async (_, { arg }: { arg: { analysisCreate: AnalysisCreate; edges?: EdgeDefinition[] } }) => {
      const newAnalysis = await insertAnalysis(session!.APIToken.accessToken, mountGroupId, arg.analysisCreate, arg.edges || []);
      await mutateAnalyses();
      await mutateEntityGraph();
      return newAnalysis;
    }
  );

  const { trigger: triggerInsertFilesDataSources } = useSWRMutation(
    ["data-sources", mountGroupId],
    async (_, { arg }: { arg: { files: File[]; edges?: EdgeDefinition[] } }) => {
      const newDataSources = await insertFilesDataSources(session!.APIToken.accessToken, mountGroupId, arg.files, arg.edges || []);
      await mutateDataSources();
      await mutateEntityGraph();
      return newDataSources;
    }
  );

  // Mutation hooks for delete operations
  const { trigger: triggerDeleteDataSource } = useSWRMutation(
    ["data-sources", mountGroupId],
    async (_, { arg }: { arg: { dataSourceId: UUID } }) => {
      await deleteDataSource(session!.APIToken.accessToken, mountGroupId, arg.dataSourceId);
      await mutateDataSources();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteDataset } = useSWRMutation(
    ["datasets", mountGroupId],
    async (_, { arg }: { arg: { datasetId: UUID } }) => {
      await deleteDataset(session!.APIToken.accessToken, mountGroupId, arg.datasetId);
      await mutateDatasets();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeletePipeline } = useSWRMutation(
    ["pipelines", mountGroupId],
    async (_, { arg }: { arg: { pipelineId: UUID } }) => {
      await deletePipeline(session!.APIToken.accessToken, mountGroupId, arg.pipelineId);
      await mutatePipelines();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteModelInstantiated } = useSWRMutation(
    ["models-instantiated", mountGroupId],
    async (_, { arg }: { arg: { modelInstantiatedId: UUID } }) => {
      await deleteModelInstantiated(session!.APIToken.accessToken, mountGroupId, arg.modelInstantiatedId);
      await mutateModelsInstantiated();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteAnalysis } = useSWRMutation(
    ["analyses", mountGroupId],
    async (_, { arg }: { arg: { analysisId: UUID } }) => {
      await deleteAnalysis(session!.APIToken.accessToken, mountGroupId, arg.analysisId);
      await mutateAnalyses();
      await mutateEntityGraph();
    }
  );

  // Run extraction mutation
  const { trigger: triggerRunExtraction, isMutating: isRunningExtraction } = useSWRMutation(
    ["ontology-extraction", mountGroupId],
    async () => {
      const response = await fetch(`${API_URL}/ontology/${mountGroupId}/run-extraction`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${session!.APIToken.accessToken}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to run extraction", errorText);
        throw new Error(`Failed to run extraction: ${response.status} ${errorText}`);
      }

      const result = await response.text();
      // Refresh all mounted entities after extraction
      await mutateDataSources();
      await mutateDatasets();
      await mutatePipelines();
      await mutateModelsInstantiated();
      await mutateAnalyses();
      await mutateEntityGraph();
      return result;
    }
  );

  return {
    // Data sources
    dataSources,
    mutateDataSources,
    dataSourcesError,
    dataSourcesLoading,

    // Datasets
    datasets,
    mutateDatasets,
    datasetsError,
    datasetsLoading,

    // Pipelines
    pipelines,
    mutatePipelines,
    pipelinesError,
    pipelinesLoading,

    // Models instantiated
    modelsInstantiated,
    mutateModelsInstantiated,
    modelsInstantiatedError,
    modelsInstantiatedLoading,

    // Analyses
    analyses,
    mutateAnalyses,
    analysesError,
    analysesLoading,

    // Entity graph
    entityGraph,
    mutateEntityGraph,
    entityGraphError,
    entityGraphLoading,

    // Insert operations
    insertDataSource: triggerInsertDataSource,
    insertDataset: triggerInsertDataset,
    insertPipeline: triggerInsertPipeline,
    insertModelInstantiated: triggerInsertModelInstantiated,
    insertAnalysis: triggerInsertAnalysis,
    insertFilesDataSources: triggerInsertFilesDataSources,

    // Delete operations
    deleteDataSource: triggerDeleteDataSource,
    deleteDataset: triggerDeleteDataset,
    deletePipeline: triggerDeletePipeline,
    deleteModelInstantiated: triggerDeleteModelInstantiated,
    deleteAnalysis: triggerDeleteAnalysis,

    // Extraction operation
    runExtraction: triggerRunExtraction,
    isRunningExtraction,

    // Convenience - check if any are loading
    isLoading: dataSourcesLoading || datasetsLoading || pipelinesLoading || 
               modelsInstantiatedLoading || analysesLoading || entityGraphLoading,
    
    // Convenience - check if any have errors
    hasError: !!(dataSourcesError || datasetsError || pipelinesError || 
                 modelsInstantiatedError || analysesError || entityGraphError),
  };
};

// =============================================================================
// Utility Hooks - Individual Mounted Entity Fetching
// =============================================================================

/**
 * Hook to fetch only data sources mounted in a project.
 * Lighter alternative to useOntology when you only need data sources.
 */
export const useMountedDataSources = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["data-sources", mountGroupId] : null,
    () => fetchMountedDataSources(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    dataSources: data,
    mutateDataSources: mutate,
    error,
    isLoading,
  };
};


export const useMountedDataSource = (dataSourceId: UUID, mountGroupId: UUID) => {
  const {dataSources} = useMountedDataSources(mountGroupId);
  return dataSources?.find(dataSource => dataSource.id === dataSourceId);
}

/**
 * Hook to fetch only datasets mounted in a project.
 * Lighter alternative to useOntology when you only need datasets.
 */
export const useMountedDatasets = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["datasets", mountGroupId] : null,
    () => fetchMountedDatasets(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    datasets: data,
    mutateDatasets: mutate,
    error,
    isLoading,
  };
};

export const useMountedDataset = (datasetId: UUID, mountGroupId: UUID) => {
  const {datasets} = useMountedDatasets(mountGroupId);
  return datasets?.find(dataset => dataset.id === datasetId);
}

/**
 * Hook to fetch only pipelines mounted in a project.
 * Lighter alternative to useOntology when you only need pipelines.
 */
export const useMountedPipelines = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["pipelines", mountGroupId] : null,
    () => fetchMountedPipelines(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    pipelines: data,
    mutatePipelines: mutate,
    error,
    isLoading,
  };
};

export const useMountedPipeline = (pipelineId: UUID, mountGroupId: UUID) => {
  const {pipelines} = useMountedPipelines(mountGroupId);
  return pipelines?.find(pipeline => pipeline.id === pipelineId);
}

/**
 * Hook to fetch only models instantiated mounted in a project.
 * Lighter alternative to useOntology when you only need models.
 */
export const useMountedModelsInstantiated = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["models-instantiated", mountGroupId] : null,
    () => fetchMountedModelsInstantiated(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    modelsInstantiated: data,
    mutateModelsInstantiated: mutate,
    error,
    isLoading,
  };
};

export const useMountedModelInstantiated = (modelInstantiatedId: UUID, mountGroupId: UUID) => {
  const {modelsInstantiated} = useMountedModelsInstantiated(mountGroupId);
  return modelsInstantiated?.find(modelInstantiated => modelInstantiated.id === modelInstantiatedId);
}

/**
 * Hook to fetch only analyses mounted in a project.
 * Lighter alternative to useOntology when you only need analyses.
 */
export const useMountedAnalyses = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["analyses", mountGroupId] : null,
    () => fetchMountedAnalyses(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    analyses: data,
    mutateAnalyses: mutate,
    error,
    isLoading,
  };
};

export const useMountedAnalysis = (analysisId: UUID, mountGroupId: UUID) => {
  const {analyses} = useMountedAnalyses(mountGroupId);
  return analyses?.find(analysis => analysis.id === analysisId);
}

/**
 * Hook to fetch only the entity graph for a project.
 * Lighter alternative to useOntology when you only need the graph structure.
 */
export const useMountedEntityGraph = (mountGroupId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["entity-graph", mountGroupId] : null,
    () => fetchEntityGraph(session!.APIToken.accessToken, mountGroupId)
  );

  return {
    entityGraph: data,
    mutateEntityGraph: mutate,
    error,
    isLoading,
  };
};



