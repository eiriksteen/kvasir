import useSWR from "swr";
import { useSession } from "next-auth/react";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { ModelInstantiated } from "@/types/ontology/model";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchModelsInstantiatedByIds(token: string, modelInstantiatedIds: UUID[]): Promise<ModelInstantiated[]> {
  const params = new URLSearchParams();
  modelInstantiatedIds.forEach(id => params.append('model_instantiated_ids', id));
  
  const response = await fetch(`${API_URL}/model/models-instantiated-by-ids?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch models instantiated: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchModelInstantiatedById(token: string, modelInstantiatedId: UUID): Promise<ModelInstantiated> {
  const response = await fetch(`${API_URL}/model/model-instantiated/${modelInstantiatedId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch model instantiated: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useModelsInstantiated = (modelInstantiatedIds?: UUID[]) => {
  const { data: session } = useSession();
  
  const { data, error, isLoading, mutate: mutateModelsInstantiated } = useSWR(
    session && modelInstantiatedIds && modelInstantiatedIds.length > 0
      ? ["models-instantiated", modelInstantiatedIds]
      : null,
    () => fetchModelsInstantiatedByIds(session ? session.APIToken.accessToken : "", modelInstantiatedIds || [])
  );

  return {
    modelsInstantiated: data,
    isLoading,
    isError: error,
    mutateModelsInstantiated,
  };
}; 

export const useModelInstantiated = (modelInstantiatedId?: UUID) => {
  const { data: session } = useSession();
  const { data: modelInstantiated, error, isLoading, mutate: mutateModelInstantiated } = useSWR(
    session && modelInstantiatedId ? ["model-instantiated", modelInstantiatedId] : null,
    () => fetchModelInstantiatedById(session ? session.APIToken.accessToken : "", modelInstantiatedId!)
  );
  return {
    modelInstantiated,
    error,
    isLoading,
    mutateModelInstantiated,
  };
};
