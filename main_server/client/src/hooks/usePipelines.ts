import useSWR, { mutate } from "swr";
import { useSession } from "next-auth/react";
import { Pipeline, PipelineRunInDB } from "@/types/pipeline";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import useSWRSubscription from "swr/subscription";
import useSWRMutation from "swr/mutation";
import { SSE } from "sse.js";
import { SWRSubscriptionOptions } from "swr/subscription";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchPipelines(token: string, projectId: UUID): Promise<Pipeline[]> {
  const response = await fetch(`${API_URL}/pipeline/project-pipelines/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch pipelines', errorText);
    throw new Error(`Failed to fetch pipelines: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

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


async function fetchPipelineRuns(token: string): Promise<PipelineRunInDB[]> {

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


function createPipelineRunsEventSource(token: string): SSE {
  return new SSE(`${API_URL}/pipeline/stream-pipeline-runs`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });
}


async function runPipeline(token: string, pipelineId: UUID, projectId: UUID): Promise<Pipeline> {
  const response = await fetch(`${API_URL}/pipeline/run-pipeline`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ pipeline_id: pipelineId, project_id: projectId }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to run pipeline', errorText);
    throw new Error(`Failed to run pipeline: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const usePipelines = (projectId: UUID) => {
  const { data: session } = useSession();
  const { data: pipelines, mutate: mutatePipelines, error, isLoading } = useSWR<Pipeline[]>(
    session ? ["pipelines", projectId] : null, 
    () => fetchPipelines(session ? session.APIToken.accessToken : "", projectId),
    {
      // revalidateOnFocus: false,
      //revalidateOnReconnect: false,
      revalidateIfStale: false,
    }
  );
  const { data: pipelineRuns, mutate: mutatePipelineRuns } = useSWR<PipelineRunInDB[]>(
    session ? "pipelineRuns" : null, () => fetchPipelineRuns(session ? session.APIToken.accessToken : "")
  );

  const { trigger: triggerRunPipeline } = useSWRMutation(
   ["pipelineRun", projectId],
     (_, { arg }: { arg: {projectId: UUID, pipelineId: UUID} }) => runPipeline(session ? session.APIToken.accessToken : "", arg.pipelineId, arg.projectId),
    {
      populateCache: (newPipeline) => newPipeline,
      revalidate: false
    }
  );

  useSWRSubscription(
    session ? ["pipelineRuns", projectId] : null,
    (_, {next}: SWRSubscriptionOptions<Pipeline[]>) => {
      const eventSource = createPipelineRunsEventSource(session ? session.APIToken.accessToken : "");

      eventSource.onmessage = (ev) => {
        const streamedPipelineRuns = snakeToCamelKeys(JSON.parse(ev.data));
        next(null, async () => {

          const runsAreUndefined = !pipelineRuns;
          const newRuns = streamedPipelineRuns.filter((run: PipelineRunInDB) => !pipelineRuns?.find((currentRun: PipelineRunInDB) => currentRun.id === run.id));
          const runsChangedStatus = streamedPipelineRuns.filter((run: PipelineRunInDB) => run.status !== pipelineRuns?.find((currentRun: PipelineRunInDB) => currentRun.id === run.id)?.status);

          // Return without changes if all streamedRuns are the same as the current runs and no run has changed status
          if (runsAreUndefined || (newRuns.length === 0 && runsChangedStatus.length === 0)) {
            return undefined;
          }

          let updatedRuns = pipelineRuns.map(run => runsChangedStatus.find((changedRun: PipelineRunInDB) => changedRun.id === run.id) || run);
          updatedRuns = updatedRuns.concat(newRuns);
          mutatePipelineRuns(updatedRuns, {revalidate: false});

          const completedRuns = runsChangedStatus.filter((run: PipelineRunInDB) => run.status === "completed");
          if (completedRuns.length > 0) {
            // When a pipeline completes we get new datasets and potentially new model entities
            mutate(["datasets", projectId]);
            mutate(["model-entities", projectId])
          }
          return undefined;
        })
      }

      return () => eventSource.close();
    }
  );

  return {
    pipelines,
    pipelineRuns: pipelineRuns || [],
    triggerRunPipeline,
    mutatePipelines,
    isLoading,
    isError: error,
  };
}; 


export const usePipeline = (pipelineId: UUID) => {
  const { data: session } = useSession();

  const { data: pipeline, isLoading: isLoadingPipeline, error: errorPipeline } = useSWR<Pipeline>(
    pipelineId ? `pipeline-${pipelineId}` : null,
    () => fetchPipeline(session ? session.APIToken.accessToken : "", pipelineId),
  );

  const { trigger: triggerRunPipeline } = useSWRMutation(
    pipelineId ? `pipeline-${pipelineId}` : null,
     (_, { arg }: { arg: {projectId: UUID} }) => runPipeline(session ? session.APIToken.accessToken : "", pipelineId, arg.projectId),
    {
      populateCache: (newPipeline) => newPipeline,
      revalidate: false
    }
  );

  return {
    pipeline,
    triggerRunPipeline,
    isLoading: isLoadingPipeline,
    isError: errorPipeline,
  };
};