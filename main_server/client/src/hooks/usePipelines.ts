import useSWR from "swr";
import { useSession } from "next-auth/react";
import { Pipeline, PipelineRunBase, PipelineRunCreate } from "@/types/ontology/pipeline";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { UUID } from "crypto";
import useSWRSubscription from "swr/subscription";
import useSWRMutation from "swr/mutation";
import { SSE } from "sse.js";
import { SWRSubscriptionOptions } from "swr/subscription";
import { useMemo } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// =============================================================================
// API Functions
// =============================================================================

async function fetchPipeline(token: string, pipelineId: UUID): Promise<Pipeline> {
  const response = await fetch(`${API_URL}/pipeline/pipelines/${pipelineId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch pipeline', errorText);
    throw new Error(`Failed to fetch pipeline: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchPipelinesByIds(token: string, pipelineIds: UUID[]): Promise<Pipeline[]> {
  const params = new URLSearchParams();
  pipelineIds.forEach(id => params.append('pipeline_ids', id));

  const response = await fetch(`${API_URL}/pipeline/pipelines-by-ids?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch pipelines by ids', errorText);
    throw new Error(`Failed to fetch pipelines by ids: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchPipelineRuns(token: string): Promise<PipelineRunBase[]> {
  const response = await fetch(`${API_URL}/pipeline/pipelines/runs`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch pipeline runs', errorText);
    throw new Error(`Failed to fetch pipeline runs: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createPipelineRun(token: string, pipelineRunCreate: PipelineRunCreate): Promise<PipelineRunBase> {
  const response = await fetch(`${API_URL}/pipeline/pipeline-run`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(pipelineRunCreate)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create pipeline run', errorText);
    throw new Error(`Failed to create pipeline run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

function createPipelineRunsEventSource(token: string): SSE {
  return new SSE(`${API_URL}/pipeline/stream-pipeline-runs`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });
}

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to fetch pipelines by IDs.
 * For fetching all pipelines in a project, use useOntology instead.
 */
export const usePipelinesByIds = (pipelineIds?: UUID[]) => {
  const { data: session } = useSession();

  const { data: pipelines, mutate: mutatePipelines, error, isLoading } = useSWR(
    session && pipelineIds && pipelineIds.length > 0 ? ["pipelines-by-ids", pipelineIds] : null,
    () => fetchPipelinesByIds(session!.APIToken.accessToken, pipelineIds || [])
  );

  return {
    pipelines,
    mutatePipelines,
    error,
    isLoading,
  };
};

/**
 * Hook to fetch a single pipeline.
 */
export const usePipeline = (pipelineId?: UUID) => {
  const { data: session } = useSession();

  const { data: pipeline, mutate: mutatePipeline, error, isLoading } = useSWR(
    session && pipelineId ? ["pipeline", pipelineId] : null,
    () => fetchPipeline(session!.APIToken.accessToken, pipelineId!)
  );

  return {
    pipeline,
    mutatePipeline,
    error,
    isLoading,
  };
};

/**
 * Hook to fetch and manage pipeline runs with real-time streaming updates.
 * 
 * This hook provides:
 * - All pipeline runs
 * - Ability to create new pipeline runs
 * - Real-time SSE streaming of pipeline run status updates
 * 
 * Note: For creating/deleting pipelines, use useOntology hook.
 */
export const usePipelineRuns = () => {
  const { data: session } = useSession();

  // Fetch pipeline runs
  const { data: pipelineRuns, mutate: mutatePipelineRuns, error, isLoading } = useSWR<PipelineRunBase[]>(
    session ? "pipeline-runs" : null,
    () => fetchPipelineRuns(session!.APIToken.accessToken),
    { fallbackData: [] }
  );

  // Create pipeline run mutation
  const { trigger: triggerCreatePipelineRun } = useSWRMutation(
    "pipeline-runs",
    async (_, { arg }: { arg: PipelineRunCreate }) => {
      const newPipelineRun = await createPipelineRun(session!.APIToken.accessToken, arg);
      await mutatePipelineRuns((currentRuns) => {
        if (currentRuns) {
          return [...currentRuns, newPipelineRun];
        }
        return [newPipelineRun];
      }, { revalidate: false });
      return newPipelineRun;
    }
  );

  // SSE streaming for pipeline run updates
  useSWRSubscription(
    session && pipelineRuns ? ["pipeline-runs-stream", pipelineRuns.length] : null,
    (_, { next }: SWRSubscriptionOptions<PipelineRunBase[]>) => {
      if (!session?.APIToken?.accessToken) return;

      const eventSource = createPipelineRunsEventSource(session.APIToken.accessToken);

      eventSource.onmessage = (ev) => {
        const streamedPipelineRuns = snakeToCamelKeys(JSON.parse(ev.data)) as PipelineRunBase[];
        
        next(null, async () => {
          await mutatePipelineRuns(async (currentRuns) => {
            if (!currentRuns) {
              return streamedPipelineRuns;
            }

            // Find new runs that don't exist in current runs
            const newRuns = streamedPipelineRuns.filter(
              (run: PipelineRunBase) => !currentRuns.find((currentRun: PipelineRunBase) => currentRun.id === run.id)
            );

            // Find runs that changed status
            const runsChangedStatus = streamedPipelineRuns.filter(
              (run: PipelineRunBase) => {
                const currentRun = currentRuns.find((currentRun: PipelineRunBase) => currentRun.id === run.id);
                return currentRun && run.status !== currentRun.status;
              }
            );

            // Return without changes if nothing new
            if (newRuns.length === 0 && runsChangedStatus.length === 0) {
              return currentRuns;
            }

            // Update existing runs with status changes and append new runs
            const updatedRuns = currentRuns.map(
              run => runsChangedStatus.find((changedRun: PipelineRunBase) => changedRun.id === run.id) || run
            ).concat(newRuns);

            return updatedRuns;
          }, { revalidate: false });

          return undefined;
        });
      };

      eventSource.onerror = (ev) => {
        console.error("Pipeline run event source error", ev);
      };

      return () => eventSource.close();
    }
  );

  return {
    pipelineRuns,
    mutatePipelineRuns,
    createPipelineRun: triggerCreatePipelineRun,
    error,
    isLoading,
  };
}; 

/**
 * Hook to get pipeline runs filtered by pipeline ID.
 */
export const usePipelineRunsByPipelineId = (pipelineId: UUID) => {
  const { pipelineRuns, mutatePipelineRuns, error, isLoading } = usePipelineRuns();

  const filteredRuns = useMemo(() => {
    return (pipelineRuns || []).filter((run: PipelineRunBase) => run.pipelineId === pipelineId);
  }, [pipelineRuns, pipelineId]);

  return {
    pipelineRuns: filteredRuns,
    mutatePipelineRuns,
    error,
    isLoading,
  };
};
