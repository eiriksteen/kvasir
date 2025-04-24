import { fetchAnalysisJobResults, postAnalysisPlanner } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import { useAgentContext } from "./useAgentContext";
export const useAnalysis = () => {
    const { data: session } = useSession();
  
    // const { data: datasetsInContext } = useSWR("datasetsInContext", { fallbackData: [] });
    // const { data: automationsInContext } = useSWR("automationsInContext", { fallbackData: [] });
    const context = useAgentContext();

    const { data: analysisJobResults, error, isLoading } = useSWR(session ? "analysisJobResults" : null, () => fetchAnalysisJobResults(session ? session.APIToken.accessToken : ""));
    const { data: currentAnalysisID } = useSWR("currentAnalysis", {fallbackData: null});

    const { trigger: createAnalysisPlanner } = useSWRMutation("createAnalysisPlanner", () => postAnalysisPlanner(session ? session.APIToken.accessToken : "", context.datasetsInContext ? context.datasetsInContext : []), {
      // populateCache: (newData) => {
      //   if (analysises) {
      //     mutateAnalysises([...analysises, newData]);
      //   }
      // }
    });
  
    // const { trigger: createAnalysis } = useSWRMutation("createAnalysis", () => postAnalysisPlanner(session ? session.APIToken.accessToken : "", datasetsInContext ? datasetsInContext : []), {
    //   populateCache: (newData) => {
    //     if (analysises) {
    //       mutateAnalysises([...analysises, newData]);
    //     }
    //     else{
    //       mutateAnalysises([newData]);
    //     }
    //     return newData.id;
    //   }
    // });
  
    return {
      currentAnalysisID,
      analysisJobResults,
      error,
      isLoading,
      createAnalysisPlanner,
      // createAnalysis,
    };
  }