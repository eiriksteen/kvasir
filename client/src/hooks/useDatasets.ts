import useSWR from "swr";
import { fetchDatasets } from "@/lib/api";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import { Dataset } from "@/types/data-objects";

export const useDatasets = () => {
  const { data: session } = useSession();
  const { data: datasets, error, isLoading } = useSWR(session ? "datasets" : null, () => fetchDatasets(session ? session.APIToken.accessToken : ""));

  return {
    datasets,
    isLoading,
    isError: error,
  };
}; 

export const useDatasetIsBeingCreated = (dataset: Dataset) => {
  return useMemo(() => {
    const isBeingCreated = !dataset?.integrationJobs?.some((job) => job.status === 'completed');
    let creationJobState;
    if (isBeingCreated) {
      creationJobState = dataset.integrationJobs?.[0]?.status;
    }
    else {
      creationJobState = "completed";
    }
    return {isBeingCreated, creationJobState};
  }, [dataset]);
};