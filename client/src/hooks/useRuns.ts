import { fetchRuns, createIncompleteRunsEventSource, fetchRunMessages, createRunMessagesEventSource } from "@/lib/api";
import { Run, RunMessage } from "@/types/runs";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import useSWR from "swr";
import { SWRSubscriptionOptions } from "swr/subscription";
import useSWRSubscription from "swr/subscription";


type runState = "running" | "failed" | "completed" | "paused" | "awaiting_approval" | "";


const computeRunState = (jobs: {id: string, status: string}[]): runState => {
  if (!jobs) return "";
  if (jobs.some(job => job.status === "running")) return "running";
  if (jobs.some(job => job.status === "paused")) return "paused";
  if (jobs.some(job => job.status === "awaiting_approval")) return "awaiting_approval";
  if (jobs.some(job => job.status === "failed")) return "failed";
  if (jobs.some(job => job.status === "completed")) return "completed";
  return "";
}

const emptyRunState: runState = ""

export const useRuns = () => {
  const { data: session } = useSession()
  const { data: runState, mutate: mutateRunState } = useSWR(["runState"], {fallbackData: emptyRunState})

  const { data: runs, mutate: mutateRuns } = useSWR(
    session ? ["runs"] : null, 
    () => fetchRuns(session ? session.APIToken.accessToken : ""), 
    {
      onSuccess: (runs: Run[]) => {
        const newRunState = computeRunState(runs);
        if (newRunState === "running" || newRunState === "paused" || newRunState === "awaiting_approval") {
          mutateRunState(newRunState, {revalidate: false});
        }
      }
    }
  )

  // This thing will always be running. Do we want to stop it when no runs are active?
  useSWRSubscription(
    session && runs ? ["runStream", runs] : null,
    (_, {next}: SWRSubscriptionOptions<Run[]>) => {
      const eventSource = createIncompleteRunsEventSource(session ? session.APIToken.accessToken : "");

      eventSource.onmessage = (ev) => {
        const streamedRuns = JSON.parse(ev.data);
        next(null, async () => {

          const runsAreUndefined = !runs;
          const newRuns = streamedRuns.filter((run: Run) => !runs?.find((currentRun: Run) => currentRun.id === run.id));
          const runsChangedStatus = streamedRuns.filter((run: Run) => run.status !== runs?.find((currentRun: Run) => currentRun.id === run.id)?.status);

          // Return without changes if all streamedRuns are the same as the current runs and no run has changed status
          if (runsAreUndefined || (newRuns.length === 0 && runsChangedStatus.length === 0)) {
            return undefined;
          }

          let updatedRuns = runs.map(run => runsChangedStatus.find((changedRun: Run) => changedRun.id === run.id) || run);
          updatedRuns = updatedRuns.concat(newRuns);

          if (updatedRuns.every((run: Run) => run.status !== "running")) {
            const newRunState = computeRunState(updatedRuns);
            mutateRunState(newRunState, {revalidate: false});
            if (newRunState == "completed" || newRunState == "failed") {
              setTimeout(() => {
                mutateRunState(emptyRunState, {revalidate: false});
              }, 5000);
            }
          }

          await mutateRuns(updatedRuns, {revalidate: false});

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

  return { runs: runs || [], runState };
};


export const useRunsInConversation = (conversationId: string) => {
  const { runs } = useRuns()

  const runsInConversation = useMemo(() => {
    return runs.filter((run: Run) => run.conversationId === conversationId)
  }, [runs, conversationId])

  return { runsInConversation }
}

export const useRun = (runId: string) => {
  const { runs } = useRuns()

  const run = useMemo(() => {
    return runs.find((run: Run) => run.id === runId)
  }, [runs, runId])

  return { run }
}

export const useRunMessages = (runId: string) => {
  const { data: session } = useSession()
  const { run } = useRun(runId)
  const { data: runMessages, mutate: mutateRunMessages } = useSWR(session ? ["runMessages", runId] : null, () => fetchRunMessages(session ? session.APIToken.accessToken : "", runId))

  useSWRSubscription(
    session && run ? ["runMessages", runId, run.status] : null,
    (_, {next}: SWRSubscriptionOptions<Run>) => {

      if (!run || !runMessages) {
        return () => {};
      }

      if (run.status === "running") {

        const eventSource = createRunMessagesEventSource(session ? session.APIToken.accessToken : "", runId)

        eventSource.onmessage = (ev) => {
          const streamedMessage: RunMessage = JSON.parse(ev.data);
          next(null, () => {
            mutateRunMessages([...(runMessages || []), streamedMessage], {revalidate: false});
            return undefined;
          })
        }

        return () => eventSource.close();
      }
      else {
        return () => {};
      }
    }
  )

  return { runMessages }
}