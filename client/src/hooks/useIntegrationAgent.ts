import { postIntegrationAgentFeedback, postIntegrationAgentApprove, createIntegrationEventSource } from "@/lib/api";
import { useCallback } from "react";
import { IntegrationAgentFeedback, IntegrationMessage } from "@/types/integration";
import { useSession } from "next-auth/react";
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import { useJobs } from "./useJobs";

/*
Endpoints:
- call-integration-agent: GET
- integration-agent-feedback: POST
- integration-agent-history: GET
- integration-agent-human-in-the-loop: WS

Flow:
Integration job started
Websocket connection established
Websocket agent state visualized
Job completion / pause signified
User provides feedback or accepts result
 */


export const useIntegrationAgent = (jobId: string) => {
  const { data: session } = useSession();
  const { updateJobs } = useJobs("integration");

  const { data: messages } = useSWRSubscription<IntegrationMessage[]>(
    ["integration-agent-stream", jobId],
    (_: string, { next }: SWRSubscriptionOptions<IntegrationMessage[]>) => {
      if (!session?.APIToken?.accessToken) {
        return;
      }
      const eventSource = createIntegrationEventSource(session.APIToken.accessToken, jobId);
      eventSource.onmessage = (event) => {
        const newMessage = JSON.parse(event.data);
        next(null, (prev) => {
          // Feels hacky, but needed to avoid duplicates. Should revisit
          const existingMessage = prev?.find(m => m.id === newMessage.id);
          if (existingMessage) return prev;
          return [...(prev || []), newMessage];
        });
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


