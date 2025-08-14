import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import useSWRSubscription, { SWRSubscriptionOptions } from 'swr/subscription'
import { AnalysisJobResultMetadata, AnalysisStatusMessage } from "@/types/analysis";
import { EventSource } from 'eventsource';

const API_URL = process.env.NEXT_PUBLIC_API_URL;



async function deleteAnalysisJobResultsDB(token: string, jobId: string): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/delete-analysis-job-results/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete analysis job results: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

async function fetchAnalysisJobResults(token: string): Promise<AnalysisJobResultMetadata[]> {
  const response = await fetch(`${API_URL}/analysis/analysis-job-results`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text()
    console.error('Failed to fetch analysis', errorText);
    throw new Error(`Failed to fetch analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

function createAnalysisEventSource(token: string, jobId: string): EventSource {
  return new EventSource(`${API_URL}/analysis/analysis-agent-sse/${jobId}`,
    {
      fetch: (input: RequestInfo | URL, init?: RequestInit) =>
        fetch(input, {
          ...init,
          headers: {
            ...init?.headers,
            Authorization: `Bearer ${token}`,
          },
        }),
    }
  );
}

export const useAnalysis = (jobId?: string) => {
    const { data: session } = useSession();
  
    // const context = useAgentContext();

    const { data: analysisJobResults, error, isLoading } = useSWR(session ? "analysisJobResults" : null, () => fetchAnalysisJobResults(session ? session.APIToken.accessToken : ""));
    const { data: currentAnalysis, mutate: mutateCurrentAnalysis } = useSWR("currentAnalysis", {fallbackData: null});
    const { data: streamedMessages, mutate: mutateStreamedMessages } = useSWR("streamedMessages", {fallbackData: []});

    useSWRSubscription<AnalysisStatusMessage[]>(
      session && jobId ? ["analysis-agent-stream", jobId] : null,
      (_: string, { next }: SWRSubscriptionOptions<AnalysisStatusMessage[]>) => {
        if (!session?.APIToken?.accessToken || !jobId) {
          return;
        }
        const eventSource = createAnalysisEventSource(session.APIToken.accessToken, jobId);
        eventSource.onmessage = (event) => {
          const newMessage = JSON.parse(event.data) as AnalysisStatusMessage;
          next(null, undefined);
          
          // Always update streamedMessages with new messages
          mutateStreamedMessages((current: AnalysisStatusMessage[] | null) => {
            const existingMessage = current?.find((m: AnalysisStatusMessage) => m.id === newMessage.id);
            if (existingMessage) return current;
            return [...(current || []), newMessage];
          }, { revalidate: false });
        };
        return () => eventSource.close();
      },         
      { fallbackData: [] }
    );

    const { trigger: deleteAnalysisJobResults } = useSWRMutation("deleteAnalysisJobResults", 
      async (_, { arg }: { arg: AnalysisJobResultMetadata }) => {
        await deleteAnalysisJobResultsDB(
          session ? session.APIToken.accessToken : "",
          arg.jobId
        );
        return arg;
      }, {
      populateCache: (newData: AnalysisJobResultMetadata) => {
        if (analysisJobResults) {
          return analysisJobResults.filter((analysis: AnalysisJobResultMetadata) => analysis.jobId !== newData.jobId);
        }
        return [];
      } 
    }); 

    

    // const { trigger: setCurrentAnalysis } = useSWRMutation(
    //   "currentAnalysis",
    //   async (_, { arg }: { arg: AnalysisJobResultMetadata | null }) => {
    //     return arg;
    //   }, {
    //   populateCache: (newData: AnalysisJobResultMetadata | null) => {
    //     return newData;
    //   }
    //   }
    // );


  
    return {
      currentAnalysis,
      streamedMessages,
      mutateCurrentAnalysis,
      analysisJobResults,
      deleteAnalysisJobResults,
      error,
      isLoading,
    };
  }