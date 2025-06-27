import { fetchModelIntegrationMessages, createModelIntegrationEventSource } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import useSWR from "swr";
import { ModelIntegrationMessage } from "@/types/model-integration";


export const useModelIntegrationAgent = (jobId: string) => {
  const { data: session } = useSession();

  const { data: messages, mutate: mutateMessages } = useSWR<ModelIntegrationMessage[]>(
    session ? ["model-integration-messages", jobId] : null,
    () => fetchModelIntegrationMessages(session ? session?.APIToken?.accessToken : "", jobId),
    {fallbackData: []}
  );

  // TODO: Add some kind of streaming pause when awaiting user input
  useSWRSubscription<ModelIntegrationMessage[]>(
    session ? ["model-integration-agent-stream", jobId] : null,
    (_: string, { next }: SWRSubscriptionOptions<ModelIntegrationMessage[]>) => {
      if (!session?.APIToken?.accessToken) {
        return;
      }
      const eventSource = createModelIntegrationEventSource(session.APIToken.accessToken, jobId);
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

  return { messages, isConnected: true };
}

