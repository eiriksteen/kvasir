import { fetchDatasets } from "@/lib/api";
import { useSession } from "next-auth/react";
import useSWR from "swr";

export const useDatasets = () => {
  const {data: session} = useSession();
  const {data, error, isLoading} = useSWR(session ? "datasets" : null, () => fetchDatasets(session ? session.APIToken.accessToken : ""));
  
  return {
    datasets: data,
    isLoading,
    isError: error,
  };
}; 