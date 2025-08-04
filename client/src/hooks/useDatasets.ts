import useSWR from "swr";
import { fetchDatasets } from "@/lib/api";
import { useSession } from "next-auth/react";

export const useDatasets = () => {
  const { data: session } = useSession();
  const { data: datasets, mutate: mutateDatasets, error, isLoading } = useSWR(session ? "datasets" : null, () => fetchDatasets(session ? session.APIToken.accessToken : ""));

  return {
    datasets,
    mutateDatasets,
    isLoading,
    isError: error,
  };
}; 
