import useSWR from "swr";
import { useSession } from "next-auth/react";
import { Pipeline } from "@/types/pipeline";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import useSWRMutation from "swr/mutation";

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



// TODO: Should set up streaming and all
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
  const { trigger: triggerRunPipeline } = useSWRMutation(
   ["pipelineRun", projectId],
     (_, { arg }: { arg: {projectId: UUID, pipelineId: UUID} }) => runPipeline(session ? session.APIToken.accessToken : "", arg.pipelineId, arg.projectId),
    {
      populateCache: (newPipeline) => newPipeline,
      revalidate: false
    }
  );

  return {
    pipelines,
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