import useSWR from "swr";
import { useSession } from "next-auth/react";
import { Pipeline } from "@/types/pipeline";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchPipelines(token: string): Promise<Pipeline[]> {
  const response = await fetch(`${API_URL}/pipeline/user-pipelines`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch pipelines', errorText);
    throw new Error(`Failed to fetch pipelines: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export const usePipelines = () => {
  const { data: session } = useSession();
  const { data: pipelines, mutate: mutatePipelines, error, isLoading } = useSWR(
    session ? "pipelines" : null, 
    () => fetchPipelines(session ? session.APIToken.accessToken : ""),
    {
      // revalidateOnFocus: false,
      //revalidateOnReconnect: false,
      revalidateIfStale: false,
    }
  );

  return {
    pipelines,
    mutatePipelines,
    isLoading,
    isError: error,
  };
}; 

