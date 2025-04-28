import { fetchAnalysisJobResults, postAnalysisPlanner } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import { Automation } from "@/types/automations";
import { TimeSeriesDataset } from "@/types/datasets";
import { useAgentContext } from "./useAgentContext";

export const useAnalysis = () => {
    const { data: session } = useSession();
  
    const context = useAgentContext();

    const { data: analysisJobResults, error, isLoading } = useSWR(session ? "analysisJobResults" : null, () => fetchAnalysisJobResults(session ? session.APIToken.accessToken : ""));
    const { data: currentAnalysisID } = useSWR("currentAnalysis", {fallbackData: null});

    const { trigger: createAnalysisPlanner } = useSWRMutation("createAnalysisPlanner", () => postAnalysisPlanner(
      session ? session.APIToken.accessToken : "", 
      context.datasetsInContext ? context.datasetsInContext.map((dataset: TimeSeriesDataset) => dataset.id) : [], 
      // context.automationsInContext ? context.automationsInContext.automations.map((automation: Automation) => automation.id) : [], 
      [],
      "Make a detailed analysis plan."), {
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