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
async function fetchMountedDataSources(token: string, mountNodeId: UUID): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/data-sources`, {
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
async function fetchMountedDatasets(token: string, mountNodeId: UUID): Promise<Dataset[]> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/datasets`, {
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
async function fetchMountedPipelines(token: string, mountNodeId: UUID): Promise<Pipeline[]> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/pipelines`, {
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
async function fetchMountedModelsInstantiated(token: string, mountNodeId: UUID): Promise<ModelInstantiated[]> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/models-instantiated`, {
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
async function fetchMountedAnalyses(token: string, mountNodeId: UUID): Promise<Analysis[]> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/analyses`, {
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
async function fetchEntityGraph(token: string, mountNodeId: UUID): Promise<EntityGraph> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/entity-graph`, {
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
  mountNodeId: UUID,
  dataSourceCreate: DataSourceCreate,
  edges: EdgeDefinition[] = []
): Promise<DataSource> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/data-source`, {
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
  mountNodeId: UUID,
  datasetCreate: DatasetCreate,
  edges: EdgeDefinition[] = []
): Promise<Dataset> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/dataset`, {
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
  mountNodeId: UUID,
  pipelineCreate: PipelineCreate,
  edges: EdgeDefinition[] = []
): Promise<Pipeline> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/pipeline`, {
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
  mountNodeId: UUID,
  modelInstantiatedCreate: ModelInstantiatedCreate,
  edges: EdgeDefinition[] = []
): Promise<ModelInstantiated> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/model-instantiated`, {
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
  mountNodeId: UUID,
  analysisCreate: AnalysisCreate,
  edges: EdgeDefinition[] = []
): Promise<Analysis> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/analysis`, {
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
  mountNodeId: UUID,
  files: File[],
  edges: EdgeDefinition[] = []
): Promise<DataSource[]> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('edges', JSON.stringify(camelToSnakeKeys(edges)));

  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/files-data-sources`, {
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
async function deleteDataSource(token: string, mountNodeId: UUID, dataSourceId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/data-source/${dataSourceId}`, {
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

async function deleteDataset(token: string, mountNodeId: UUID, datasetId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/dataset/${datasetId}`, {
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

async function deletePipeline(token: string, mountNodeId: UUID, pipelineId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/pipeline/${pipelineId}`, {
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

async function deleteModelInstantiated(token: string, mountNodeId: UUID, modelInstantiatedId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/model-instantiated/${modelInstantiatedId}`, {
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

async function deleteAnalysis(token: string, mountNodeId: UUID, analysisId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/analysis/${analysisId}`, {
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

async function deleteEntityBranch(token: string, mountNodeId: UUID, nodeId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/ontology/${mountNodeId}/entity-branch/${nodeId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete entity branch: ${response.status} ${errorText}`);
  }
}

/**
 * Hook for accessing ontology methods for a specific project (mount group).
 * This mirrors the backend Ontology class and provides convenient access to
 * all entities mounted in a project.
 * 
 * @param mountNodeId - Required UUID of the project/mount node
 */
export const useOntology = (mountNodeId: UUID) => {
  const { data: session } = useSession();

  // Fetch mounted data sources
  const { 
    data: dataSources, 
    mutate: mutateDataSources, 
    error: dataSourcesError, 
    isLoading: dataSourcesLoading 
  } = useSWR(
    session && mountNodeId ? ["data-sources", mountNodeId] : null,
    () => fetchMountedDataSources(session!.APIToken.accessToken, mountNodeId!)
  );

  // Fetch mounted datasets
  const { 
    data: datasets, 
    mutate: mutateDatasets, 
    error: datasetsError, 
    isLoading: datasetsLoading 
  } = useSWR(
    session && mountNodeId ? ["datasets", mountNodeId] : null,
    () => fetchMountedDatasets(session!.APIToken.accessToken, mountNodeId!)
  );

  // Fetch mounted pipelines
  const { 
    data: pipelines, 
    mutate: mutatePipelines, 
    error: pipelinesError, 
    isLoading: pipelinesLoading 
  } = useSWR(
    session && mountNodeId ? ["pipelines", mountNodeId] : null,
    () => fetchMountedPipelines(session!.APIToken.accessToken, mountNodeId!)
  );

  // Fetch mounted models instantiated
  const { 
    data: modelsInstantiated, 
    mutate: mutateModelsInstantiated, 
    error: modelsInstantiatedError, 
    isLoading: modelsInstantiatedLoading 
  } = useSWR(
    session && mountNodeId ? ["models-instantiated", mountNodeId] : null,
    () => fetchMountedModelsInstantiated(session!.APIToken.accessToken, mountNodeId!)
  );

  // Fetch mounted analyses
  const { 
    data: analyses, 
    mutate: mutateAnalyses, 
    error: analysesError, 
    isLoading: analysesLoading 
  } = useSWR(
    session && mountNodeId ? ["analyses", mountNodeId] : null,
    () => fetchMountedAnalyses(session!.APIToken.accessToken, mountNodeId!)
  );

  // Fetch entity graph
  const { 
    data: entityGraph, 
    mutate: mutateEntityGraph, 
    error: entityGraphError, 
    isLoading: entityGraphLoading 
  } = useSWR(
    session && mountNodeId ? ["entity-graph", mountNodeId] : null,
    () => fetchEntityGraph(session!.APIToken.accessToken, mountNodeId!)
  );

  // Mutation hooks for insert operations
  const { trigger: triggerInsertDataSource } = useSWRMutation(
    ["data-sources", mountNodeId],
    async (_, { arg }: { arg: { dataSourceCreate: DataSourceCreate; edges?: EdgeDefinition[] } }) => {
      const newDataSource = await insertDataSource(session!.APIToken.accessToken, mountNodeId, arg.dataSourceCreate, arg.edges || []);
      await mutateDataSources();
      await mutateEntityGraph();
      return newDataSource;
    }
  );

  const { trigger: triggerInsertDataset } = useSWRMutation(
    ["datasets", mountNodeId],
    async (_, { arg }: { arg: { datasetCreate: DatasetCreate; edges?: EdgeDefinition[] } }) => {
      const newDataset = await insertDataset(session!.APIToken.accessToken, mountNodeId, arg.datasetCreate, arg.edges || []);
      await mutateDatasets();
      await mutateEntityGraph();
      return newDataset;
    }
  );

  const { trigger: triggerInsertPipeline } = useSWRMutation(
    ["pipelines", mountNodeId],
    async (_, { arg }: { arg: { pipelineCreate: PipelineCreate; edges?: EdgeDefinition[] } }) => {
      const newPipeline = await insertPipeline(session!.APIToken.accessToken, mountNodeId, arg.pipelineCreate, arg.edges || []);
      await mutatePipelines();
      await mutateEntityGraph();
      return newPipeline;
    }
  );

  const { trigger: triggerInsertModelInstantiated } = useSWRMutation(
    ["models-instantiated", mountNodeId],
    async (_, { arg }: { arg: { modelInstantiatedCreate: ModelInstantiatedCreate; edges?: EdgeDefinition[] } }) => {
      const newModel = await insertModelInstantiated(session!.APIToken.accessToken, mountNodeId, arg.modelInstantiatedCreate, arg.edges || []);
      await mutateModelsInstantiated();
      await mutateEntityGraph();
      return newModel;
    }
  );

  const { trigger: triggerInsertAnalysis } = useSWRMutation(
    ["analyses", mountNodeId],
    async (_, { arg }: { arg: { analysisCreate: AnalysisCreate; edges?: EdgeDefinition[] } }) => {
      const newAnalysis = await insertAnalysis(session!.APIToken.accessToken, mountNodeId, arg.analysisCreate, arg.edges || []);
      await mutateAnalyses();
      await mutateEntityGraph();
      return newAnalysis;
    }
  );

  const { trigger: triggerInsertFilesDataSources } = useSWRMutation(
    ["data-sources", mountNodeId],
    async (_, { arg }: { arg: { files: File[]; edges?: EdgeDefinition[] } }) => {
      const newDataSources = await insertFilesDataSources(session!.APIToken.accessToken, mountNodeId, arg.files, arg.edges || []);
      await mutateDataSources();
      await mutateEntityGraph();
      return newDataSources;
    }
  );

  // Mutation hooks for delete operations
  const { trigger: triggerDeleteDataSource } = useSWRMutation(
    ["data-sources", mountNodeId],
    async (_, { arg }: { arg: { dataSourceId: UUID } }) => {
      await deleteDataSource(session!.APIToken.accessToken, mountNodeId, arg.dataSourceId);
      await mutateDataSources();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteDataset } = useSWRMutation(
    ["datasets", mountNodeId],
    async (_, { arg }: { arg: { datasetId: UUID } }) => {
      await deleteDataset(session!.APIToken.accessToken, mountNodeId, arg.datasetId);
      await mutateDatasets();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeletePipeline } = useSWRMutation(
    ["pipelines", mountNodeId],
    async (_, { arg }: { arg: { pipelineId: UUID } }) => {
      await deletePipeline(session!.APIToken.accessToken, mountNodeId, arg.pipelineId);
      await mutatePipelines();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteModelInstantiated } = useSWRMutation(
    ["models-instantiated", mountNodeId],
    async (_, { arg }: { arg: { modelInstantiatedId: UUID } }) => {
      await deleteModelInstantiated(session!.APIToken.accessToken, mountNodeId, arg.modelInstantiatedId);
      await mutateModelsInstantiated();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteAnalysis } = useSWRMutation(
    ["analyses", mountNodeId],
    async (_, { arg }: { arg: { analysisId: UUID } }) => {
      await deleteAnalysis(session!.APIToken.accessToken, mountNodeId, arg.analysisId);
      await mutateAnalyses();
      await mutateEntityGraph();
    }
  );

  const { trigger: triggerDeleteEntityBranch } = useSWRMutation(
    ["entity-graph", mountNodeId],
    async (_, { arg }: { arg: { nodeId: UUID } }) => {
      await deleteEntityBranch(session!.APIToken.accessToken, mountNodeId, arg.nodeId);
      await mutateDataSources();
      await mutateDatasets();
      await mutatePipelines();
      await mutateModelsInstantiated();
      await mutateAnalyses();
      await mutateEntityGraph();
    }
  );

  // Run extraction mutation
  const { trigger: triggerRunExtraction, isMutating: isRunningExtraction } = useSWRMutation(
    ["ontology-extraction", mountNodeId],
    async () => {
      const response = await fetch(`${API_URL}/ontology/${mountNodeId}/run-extraction`, {
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
    deleteEntityBranch: triggerDeleteEntityBranch,

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
export const useMountedDataSources = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["data-sources", mountNodeId] : null,
    () => fetchMountedDataSources(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    dataSources: data,
    mutateDataSources: mutate,
    error,
    isLoading,
  };
};


export const useMountedDataSource = (dataSourceId: UUID, mountNodeId: UUID) => {
  const {dataSources} = useMountedDataSources(mountNodeId);
  return dataSources?.find(dataSource => dataSource.id === dataSourceId);
}

/**
 * Hook to fetch only datasets mounted in a project.
 * Lighter alternative to useOntology when you only need datasets.
 */
export const useMountedDatasets = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["datasets", mountNodeId] : null,
    () => fetchMountedDatasets(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    datasets: data,
    mutateDatasets: mutate,
    error,
    isLoading,
  };
};

export const useMountedDataset = (datasetId: UUID, mountNodeId: UUID) => {
  const {datasets} = useMountedDatasets(mountNodeId);
  return datasets?.find(dataset => dataset.id === datasetId);
}

/**
 * Hook to fetch only pipelines mounted in a project.
 * Lighter alternative to useOntology when you only need pipelines.
 */
export const useMountedPipelines = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["pipelines", mountNodeId] : null,
    () => fetchMountedPipelines(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    pipelines: data,
    mutatePipelines: mutate,
    error,
    isLoading,
  };
};

export const useMountedPipeline = (pipelineId: UUID, mountNodeId: UUID) => {
  const {pipelines} = useMountedPipelines(mountNodeId);
  return pipelines?.find(pipeline => pipeline.id === pipelineId);
}

/**
 * Hook to fetch only models instantiated mounted in a project.
 * Lighter alternative to useOntology when you only need models.
 */
export const useMountedModelsInstantiated = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["models-instantiated", mountNodeId] : null,
    () => fetchMountedModelsInstantiated(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    modelsInstantiated: data,
    mutateModelsInstantiated: mutate,
    error,
    isLoading,
  };
};

export const useMountedModelInstantiated = (modelInstantiatedId: UUID, mountNodeId: UUID) => {
  const {modelsInstantiated} = useMountedModelsInstantiated(mountNodeId);
  return modelsInstantiated?.find(modelInstantiated => modelInstantiated.id === modelInstantiatedId);
}

/**
 * Hook to fetch only analyses mounted in a project.
 * Lighter alternative to useOntology when you only need analyses.
 */
export const useMountedAnalyses = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["analyses", mountNodeId] : null,
    () => fetchMountedAnalyses(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    analyses: data,
    mutateAnalyses: mutate,
    error,
    isLoading,
  };
};

export const useMountedAnalysis = (analysisId: UUID, mountNodeId: UUID) => {
  const {analyses} = useMountedAnalyses(mountNodeId);
  return analyses?.find(analysis => analysis.id === analysisId);
}

/**
 * Hook to fetch only the entity graph for a project.
 * Lighter alternative to useOntology when you only need the graph structure.
 */
export const useMountedEntityGraph = (mountNodeId: UUID) => {
  const { data: session } = useSession();
  const { data, mutate, error, isLoading } = useSWR(
    session && mountNodeId ? ["entity-graph", mountNodeId] : null,
    () => fetchEntityGraph(session!.APIToken.accessToken, mountNodeId)
  );

  return {
    entityGraph: data,
    mutateEntityGraph: mutate,
    error,
    isLoading,
  };
};



