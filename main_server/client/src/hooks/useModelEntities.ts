import useSWR from "swr";
import { useSession } from "next-auth/react";
import { ModelEntity } from "@/types/model";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { useMemo } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchModelEntities(token: string, projectId: UUID): Promise<ModelEntity[]> {
  const response = await fetch(`${API_URL}/model/project-model-entities/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch model entities: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useModelEntities = (projectId: UUID) => {
  const {data: session} = useSession();
  const {data, error, isLoading} = useSWR(session ? ["model-entities", projectId] : null, () => fetchModelEntities(session ? session.APIToken.accessToken : "", projectId));

  return {
    modelEntities: data,
    isLoading,
    isError: error,
  };
}; 

export const useModelEntity = (projectId: UUID, modelEntityId: UUID) => {
  const { modelEntities: models } = useModelEntities(projectId);

  const modelEntity = useMemo(() => models?.find(modelEntity => modelEntity.id === modelEntityId), [models, modelEntityId]);

  return {
    modelEntity,
  };
};
