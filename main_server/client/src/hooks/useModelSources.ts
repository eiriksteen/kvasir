import useSWR from "swr";
import { useSession } from "next-auth/react";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { ModelSource } from "@/types/model-source";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchModelSources(token: string, projectId: UUID): Promise<ModelSource[]> {
  const response = await fetch(`${API_URL}/model-sources/project-model-sources/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch model sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useModelSources = (projectId: UUID) => {
  const {data: session} = useSession();
  const {data, error, isLoading} = useSWR(session ? ["model-sources", projectId] : null, () => fetchModelSources(session ? session.APIToken.accessToken : "", projectId));

  return {
    modelSources: data,
    isLoading,
    isError: error,
  };
};