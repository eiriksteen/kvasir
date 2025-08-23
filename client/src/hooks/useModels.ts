import { useSession } from "next-auth/react";
import useSWR from "swr";
import { Model } from "@/types/pipeline";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchModels(token: string, only_owned: boolean = false): Promise<Model[]> {
  const route = only_owned  ? "/automation/models/my?include_integration_jobs=1" : "/automation/models?include_integration_jobs=1";
  const response = await fetch(`${API_URL}${route}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch models', errorText);
    throw new Error(`Failed to fetch models: ${response.status} ${errorText}`);
  }

  return response.json();
}

export const useModels = () => {
  const {data: session} = useSession();
  const {data, error, isLoading} = useSWR(session ? "models" : null, () => fetchModels(session ? session.APIToken.accessToken : "", true));

  return {
    models: data,
    isLoading,
    isError: error,
  };
}; 

