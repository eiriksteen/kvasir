import { fetchModels } from "@/lib/api";
import { Model } from "@/types/model-integration";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import useSWR from "swr";

export const useModels = () => {
  const {data: session} = useSession();
  const {data, error, isLoading} = useSWR(session ? "models" : null, () => fetchModels(session ? session.APIToken.accessToken : "", true));

  return {
    models: data,
    isLoading,
    isError: error,
  };
}; 

export const useModelIsBeingCreated = (model: Model) => {
  return useMemo(() => {
    const isBeingCreated = !model?.integration_jobs?.some((job) => job.status === 'completed');
    let creationJobState;
    if (isBeingCreated) {
      creationJobState = model.integration_jobs?.[0]?.status;
    }
    else {
      creationJobState = "completed";
    }
    return {isBeingCreated, creationJobState};
  }, [model]);
};