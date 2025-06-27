import { postIntegrationAgentFeedback, postIntegrationAgentApprove, createIntegrationEventSource, fetchIntegrationMessages } from "@/lib/api";
import { useCallback } from "react";
import { IntegrationAgentFeedback, IntegrationMessage } from "@/types/integration";
import { useSession } from "next-auth/react";
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import { useJobs } from "./useJobs";
import useSWR from "swr";


export const useIntegrationAgent = (jobId: string) => {
  const { data: session } = useSession();
  const { updateJobs } = useJobs("integration");

  const { data: messages, mutate: mutateMessages } = useSWR<IntegrationMessage[]>(
    session ? ["integration-messages", jobId] : null,
    () => fetchIntegrationMessages(session ? session?.APIToken?.accessToken : "", jobId),
    { fallbackData: [] }
  );

  // TODO: Add some kind of streaming pause when awaiting user input
  useSWRSubscription<IntegrationMessage[]>(
    session ? ["integration-agent-stream", jobId] : null,
    (_: string, { next }: SWRSubscriptionOptions<IntegrationMessage[]>) => {
      if (!session?.APIToken?.accessToken) {
        return;
      }
      const eventSource = createIntegrationEventSource(session.APIToken.accessToken, jobId);
      eventSource.onmessage = (event) => {
        const newMessage = JSON.parse(event.data);
        next(null, undefined);
        // Update the messages list from the initial fetch
        mutateMessages((current) => {
          const existingMessage = current?.find(m => m.id === newMessage.id);
          if (existingMessage) return current;
          return [...(current || []), newMessage];
        }, { revalidate: false });
      };
      return () => eventSource.close();
    },         
    { fallbackData: [] }
  );

  const submitFeedback = useCallback(async (content: string) => {
    if (session?.APIToken?.accessToken) {
      const feedback : IntegrationAgentFeedback = {
        job_id: jobId,
        content: content
      }
      try {
        await postIntegrationAgentFeedback(session.APIToken.accessToken, feedback);
        updateJobs([{id: jobId, status: "running"}]);
      } catch (error) {
        console.error("Failed to post feedback:", error);
      }
      
    }
  }, [jobId, session?.APIToken?.accessToken, updateJobs]);

  const submitApproval = useCallback(async () => {
    if (session?.APIToken?.accessToken) {
      await postIntegrationAgentApprove(session.APIToken.accessToken, jobId);
      updateJobs([{id: jobId, status: "completed"}]);
    }
  }, [jobId, session?.APIToken?.accessToken, updateJobs]);

  return {messages, submitFeedback, submitApproval, isConnected: true};
}

