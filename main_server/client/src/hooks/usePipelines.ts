import useSWR, { mutate } from "swr";
import { useSession } from "next-auth/react";
import { Pipeline, PipelineRunInDB } from "@/types/pipeline";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import useSWRSubscription from "swr/subscription";
import useSWRMutation from "swr/mutation";
import { SSE } from "sse.js";
import { SWRSubscriptionOptions } from "swr/subscription";
import { useCallback } from "react";
import { useMemo } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchPipelines(token: string, projectId: UUID): Promise<Pipeline[]> {
  console.log('fetchPipelines', projectId);
  const response = await fetch(`${API_URL}/project/project-pipelines/${projectId}`, {
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


async function runPipeline(token: string, pipelineId: UUID, projectId: UUID): Promise<PipelineRunInDB> {
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
    session ? ["pipelineRuns", projectId] : null, () => fetchPipelineRuns(session ? session.APIToken.accessToken : "")
  );

  const { trigger: triggerRunPipeline } = useSWRMutation(
    session ? ["pipelineRuns", projectId] : null,
     (_, { arg }: { arg: {projectId: UUID, pipelineId: UUID} }) => runPipeline(session ? session.APIToken.accessToken : "", arg.pipelineId, arg.projectId),
    {
      populateCache: (newPipelineRun) => {
        if (pipelineRuns) {
          return [...pipelineRuns, newPipelineRun];
        }
        return [newPipelineRun];
      },
      revalidate: false
    }
  );

  useSWRSubscription(
    session && pipelineRuns ? ["pipelineRunsStream", pipelineRuns] : null,
    (_, {next}: SWRSubscriptionOptions<PipelineRunInDB[]>) => {
      const eventSource = createPipelineRunsEventSource(session ? session.APIToken.accessToken : "");

      eventSource.onmessage = (ev) => {
        const streamedPipelineRuns = snakeToCamelKeys(JSON.parse(ev.data));
        next(null, async () => {

          await mutatePipelineRuns(async (currentRuns) => {
            if (!currentRuns) {
              return streamedPipelineRuns;
            }

            const newRuns = streamedPipelineRuns.filter((run: PipelineRunInDB) => !currentRuns.find((currentRun: PipelineRunInDB) => currentRun.id === run.id));
            const runsChangedStatus = streamedPipelineRuns.filter((run: PipelineRunInDB) => run.status !== currentRuns.find((currentRun: PipelineRunInDB) => currentRun.id === run.id)?.status);

            // Return without changes if all streamedRuns are the same as the current runs and no run has changed status
            if (newRuns.length === 0 && runsChangedStatus.length === 0) {
              return currentRuns;
            }

            // Update existing runs with status changes and append new runs
            let updatedRuns = currentRuns.map(run => runsChangedStatus.find((changedRun: PipelineRunInDB) => changedRun.id === run.id) || run);
            updatedRuns = updatedRuns.concat(newRuns);

            // Trigger project refresh if any runs completed
            const completedRuns = runsChangedStatus.filter((run: PipelineRunInDB) => run.status === "completed");
            if (completedRuns.length > 0) {
              
              // When a pipeline completes we get new datasets and potentially new model entities
              await mutate(["datasets", projectId]);
              await mutate(["model-entities", projectId])
              await mutate("projects");
              await mutate(["project-graph", projectId]);
            }

            return updatedRuns;
          }, {revalidate: false});

          // Return undefined since this is purely to update the pipeline runs by listening to updates from the event source
          return undefined;
        });
      }
      eventSource.onerror = (ev) => {
        console.error("Pipeline run event source error", ev);
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


export const usePipeline = (pipelineId: UUID, projectId: UUID) => {
  const { pipelines, mutatePipelines, triggerRunPipeline: runPipeline, pipelineRuns } = usePipelines(projectId);

  const pipeline = useMemo(() => {
    return pipelines?.find((pipeline: Pipeline) => pipeline.id === pipelineId);
  }, [pipelines, pipelineId]);

  const triggerRunPipeline = useCallback(() => {
    runPipeline({pipelineId: pipelineId, projectId: projectId});
  }, [projectId, pipelineId, runPipeline]);

  const pipelineRuns_ = useMemo(() => {
    return pipelineRuns.filter((run: PipelineRunInDB) => run.pipelineId === pipelineId);
  }, [pipelineRuns, pipelineId]);

  return {
    pipeline,
    triggerRunPipeline,
    mutatePipeline: mutatePipelines,
    pipelineRuns: pipelineRuns_
  };
};