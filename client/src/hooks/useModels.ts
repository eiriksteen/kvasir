import { fetchModels } from "@/lib/api";
import { useSession } from "next-auth/react";
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

