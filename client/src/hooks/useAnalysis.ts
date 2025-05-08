import { fetchAnalysisJobResults, deleteAnalysisJobResultsDB } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import { useAgentContext } from "./useAgentContext";
import { AnalysisJobResultMetadata } from "@/types/analysis";

export const useAnalysis = () => {
    const { data: session } = useSession();
  
    const context = useAgentContext();

    const { data: analysisJobResults, error, isLoading } = useSWR(session ? "analysisJobResults" : null, () => fetchAnalysisJobResults(session ? session.APIToken.accessToken : ""));
    const { data: currentAnalysisID } = useSWR("currentAnalysis", {fallbackData: null});


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

  
    return {
      currentAnalysisID,
      analysisJobResults,
      deleteAnalysisJobResults,
      error,
      isLoading,
    };
  }