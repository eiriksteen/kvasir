import { fetchAnalysisJobResults, deleteAnalysisJobResultsDB, createAnalysisEventSource } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import useSWRSubscription, { SWRSubscriptionOptions } from 'swr/subscription'
//import { useAgentContext } from "./useAgentContext";
import { AnalysisJobResultMetadata, AnalysisStatusMessage } from "@/types/analysis";

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
          return analysisJobResults.analysesJobResults.filter((analysis: AnalysisJobResultMetadata) => analysis.jobId !== newData.jobId);
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