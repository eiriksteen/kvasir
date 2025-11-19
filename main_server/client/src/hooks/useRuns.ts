import { RunBase, Message} from "@/types/kvasirV1";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import useSWR, { useSWRConfig } from "swr";
import { SWRSubscriptionOptions } from "swr/subscription";
import useSWRSubscription from "swr/subscription";
import { SSE } from 'sse.js';
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import useSWRMutation from "swr/mutation";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchRuns(token: string, projectId?: UUID): Promise<RunBase[]> {
  const url = projectId 
    ? `${API_URL}/kvasir-v1/runs?project_id=${projectId}`
    : `${API_URL}/kvasir-v1/runs`;
    
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch runs', errorText);
    throw new Error(`Failed to fetch runs: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
} 

async function fetchRunMessages(token: string, runId: UUID): Promise<Message[]> {
  const response = await fetch(`${API_URL}/kvasir-v1/messages/${runId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch run full: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

function createIncompleteRunsEventSource(token: string, projectId?: UUID): SSE {
  const url = projectId
    ? `${API_URL}/kvasir-v1/stream-incomplete-runs?project_id=${projectId}`
    : `${API_URL}/kvasir-v1/stream-incomplete-runs`;
    
  return new SSE(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });
}

function createProjectRunMessagesEventSource(token: string, projectId: UUID): SSE {
  return new SSE(`${API_URL}/kvasir-v1/stream-messages?project_id=${projectId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });
}


export async function launchRun(token: string, runId: UUID): Promise<RunBase> {
  const response = await fetch(`${API_URL}/kvasir-v1/launch-run/${runId}`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to launch run', errorText);
    throw new Error(`Failed to launch run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);

}

async function rejectRun(token: string, runId: UUID): Promise<RunBase> {
  const response = await fetch(`${API_URL}/kvasir-v1/reject-run/${runId}`, {
    method: "PATCH",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to reject run', errorText);
    throw new Error(`Failed to reject run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


type runState = "running" | "failed" | "completed" | "paused" | "awaiting_approval" | "rejected" | "";


const computeRunState = (jobs: {id: string, status: string}[]): runState => {
  if (!jobs) return "";
  if (jobs.some(job => job.status === "running")) return "running";
  if (jobs.some(job => job.status === "paused")) return "paused";
  if (jobs.some(job => job.status === "awaiting_approval")) return "awaiting_approval";
  if (jobs.some(job => job.status === "failed")) return "failed";
  if (jobs.some(job => job.status === "completed")) return "completed";
  if (jobs.some(job => job.status === "rejected")) return "rejected";
  return "";
}

const emptyRunState: runState = ""

export const useRuns = (projectId: UUID) => {
  const { data: session } = useSession()
  const { data: runState, mutate: mutateRunState } = useSWR([projectId, "runState"], {fallbackData: emptyRunState})
  const { mutate } = useSWRConfig()

  const { data: runs, mutate: mutateRuns } = useSWR(
    session && projectId ? ["runs", projectId] : null, 
    () => fetchRuns(session ? session.APIToken.accessToken : "", projectId), 
    {
      onSuccess: (runs: RunBase[]) => {
        const newRunState = computeRunState(runs);
        if (newRunState === "running" || newRunState === "paused" || newRunState === "awaiting_approval" || newRunState === "rejected") {
          mutateRunState(newRunState, {revalidate: false});
        }
      }
    }
  )

  const { trigger: triggerLaunchRun } = useSWRMutation(
    session && projectId ? ["runs", projectId] : null,
    (_, { arg }: { arg: {runId: UUID} }) => launchRun(session ? session.APIToken.accessToken : "", arg.runId),
    {
      populateCache: (newRun) => {
        // Replace run with newRun if run with same ID exists, else append newRun
        if (runs) {
          if (runs.some((run: RunBase) => run.id === newRun.id)) {
            return runs.map((run: RunBase) => run.id === newRun.id ? newRun : run);
          } else {
            return [...runs, newRun];
          }
        }
        return [newRun];
      },
      revalidate: false
    }
  )


  const { trigger: triggerRejectRun } = useSWRMutation(
    session && projectId ? ["runs", projectId] : null,
    (_, { arg }: { arg: {runId: UUID} }) => rejectRun(session ? session.APIToken.accessToken : "", arg.runId),
    {
      populateCache: (newRun) => {
        if (runs) {
          if (runs.some((run: RunBase) => run.id === newRun.id)) {
            return runs.map((run: RunBase) => run.id === newRun.id ? newRun : run);
          } else {
            return [...runs, newRun];
          }
        }
        return [newRun];
      },
      revalidate: false
    }
  )

  // This thing will always be running. Do we want to stop it when no runs are active?
  useSWRSubscription(
    session && runs && projectId ? ["runStream", projectId, runs] : null,
    (_, {next}: SWRSubscriptionOptions<RunBase[]>) => {
      const eventSource = createIncompleteRunsEventSource(session ? session.APIToken.accessToken : "", projectId);

      eventSource.onmessage = (ev) => {
        const streamedRuns = snakeToCamelKeys(JSON.parse(ev.data));
        next(null, async () => {

          await mutateRuns((currentRuns) => {
            if (!currentRuns) {
              return streamedRuns;
            }

            const newRuns = streamedRuns.filter((run: RunBase) => !currentRuns.find((currentRun: RunBase) => currentRun.id === run.id));
            const runsChangedStatus = streamedRuns.filter((run: RunBase) => run.status !== currentRuns.find((currentRun: RunBase) => currentRun.id === run.id)?.status);

            // Return without changes if all streamedRuns are the same as the current runs and no run has changed status
            if (newRuns.length === 0 && runsChangedStatus.length === 0) {
              return currentRuns;
            }

            // Update existing runs with status changes and append new runs
            let updatedRuns = currentRuns.map(run => runsChangedStatus.find((changedRun: RunBase) => changedRun.id === run.id) || run);
            updatedRuns = updatedRuns.concat(newRuns);

            // Update run state based on the updated runs
            const newRunState = computeRunState(updatedRuns);
            if (updatedRuns.every((run: RunBase) => run.status !== "running")) {
              mutateRunState(newRunState, {revalidate: false});
              const noRunningRuns = updatedRuns.filter((run: RunBase) => run.status === "running").length === 0;
              if (noRunningRuns) {
                setTimeout(() => {
                  mutateRunState(emptyRunState, {revalidate: false});
                }, 5000);
              }
            }

            // Trigger project refresh if any runs completed
            const completedRuns = runsChangedStatus.filter((run: RunBase) => run.status === "completed");
            if (completedRuns.length > 0) {
              mutate("projects");
            }

            return updatedRuns;
          }, {revalidate: false});

          // Return undefined since this is purely to update the jobs by listening to updates from the event source
          return undefined;
        });
      }
      eventSource.onerror = (ev) => {
        console.error("Run event source error", ev);
      }

      return () => eventSource.close();
    }
  )

  // final duplicate removal. should be dealt with in the event stream, but sometimes it doesn't work
  // todo: remove?
  const uniqueRuns = useMemo(() => {
    if (!runs) return [];
    return Array.from(new Map(runs.map(run => [run.id, run])).values());
  }, [runs]);

  return { runs: uniqueRuns, runState, triggerLaunchRun, triggerRejectRun };
};


export const useKvasirRuns = (projectId: UUID) => {
  const { runs, triggerLaunchRun } = useRuns(projectId)

  const kvasirRuns = useMemo(() => {
    return runs.filter((run: RunBase) => run.type === "kvasir")
  }, [runs])

  return { kvasirRuns, triggerLaunchRun }
}


export const useRun = (projectId: UUID, runId: UUID) => {
  const { runs, triggerLaunchRun, triggerRejectRun } = useRuns(projectId)

  const run = useMemo(() => {
    return runs.find((run: RunBase) => run.id === runId)
  }, [runs, runId])

  return { run, triggerLaunchRun, triggerRejectRun }
}


export const useProjectRunMessages = (projectId: UUID) => {
  const { data: session } = useSession()
  const { runs } = useRuns(projectId)
  const { mutate } = useSWRConfig()

  const { data: projectRunMessages, mutate: mutateProjectRunMessages } = useSWR<Record<string, Message[]>>(
    session && projectId ? ["projectRunMessages", projectId] : null, 
    async () => {
      // Fetch messages for all runs in the project
      const messagesPromises = runs.map(async (run) => {
        const messages = await fetchRunMessages(session!.APIToken.accessToken, run.id);
        return { runId: run.id, messages };
      });
      const messagesResults = await Promise.all(messagesPromises);
      
      // Convert to record of runId -> messages[]
      const messagesRecord: Record<string, Message[]> = {};
      messagesResults.forEach(({ runId, messages }) => {
        messagesRecord[runId] = messages;
      });
      return messagesRecord;
    }
  )

  const hasRunningRuns = useMemo(() => {
    return runs.some(run => run.status === "running");
  }, [runs])

  useSWRSubscription(
    session && runs.length > 0 && projectId ? ["projectRunMessagesStream", projectId, hasRunningRuns] : null,
    (_, {next}: SWRSubscriptionOptions<Record<string, Message[]>>) => {

      if (!projectRunMessages) {
        return () => {};
      }
      
      if (hasRunningRuns) {
        const eventSource = createProjectRunMessagesEventSource(session!.APIToken.accessToken, projectId)

        eventSource.onmessage = (ev) => {
          const streamedMessage: Message = snakeToCamelKeys(JSON.parse(ev.data));
          next(null, () => {
            mutateProjectRunMessages((current) => {
              if (!current) return { [streamedMessage.runId]: [streamedMessage] };
              
              return {
                ...current,
                [streamedMessage.runId]: [...(current[streamedMessage.runId] || []), streamedMessage]
              };
            }, {revalidate: false});
            return undefined;
          })

          if (streamedMessage.type === "result") {
            if (streamedMessage.content.includes("CREATED")) {
              mutate(["entity-graph", projectId]);
              if (streamedMessage.content.includes("CREATED DATA SOURCE")) {
                mutate(["data-sources", projectId]);
                mutate("projects");
              }
              if (streamedMessage.content.includes("CREATED DATASET")) {
                mutate(["datasets", projectId]);
                mutate("projects");
              }
              if (streamedMessage.content.includes("CREATED PIPELINE")) {
                mutate(["pipelines", projectId]);
                mutate("projects");
              }
              if (streamedMessage.content.includes("CREATED MODEL INSTANTIATED")) {
                mutate(["models-instantiated", projectId]);
              } 
            }
          }
        }

        return () => eventSource.close();
      }
      else {
        return () => {};
      }
    }
  )

  return { projectRunMessages: projectRunMessages || {} }
}


export const useRunMessages = (projectId: UUID, runId: UUID) => {
  const { projectRunMessages } = useProjectRunMessages(projectId)

  const runMessages = useMemo(() => {
    return projectRunMessages[runId] || []
  }, [projectRunMessages, runId])

  return { runMessages }
}

