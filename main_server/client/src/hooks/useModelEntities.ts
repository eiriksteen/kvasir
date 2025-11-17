import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSession } from "next-auth/react";
import { ModelInstantiated } from "@/types/model";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { useMemo } from "react";
import { mutate } from "swr";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchModelEntities(token: string, projectId: UUID): Promise<ModelInstantiated[]> {
  const response = await fetch(`${API_URL}/project/project-models-instantiated/${projectId}`, {
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

async function deleteModelEntityEndpoint(token: string, modelInstantiatedId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/deletion/model-instantiated/${modelInstantiatedId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete model entity', errorText);
    throw new Error(`Failed to delete model entity: ${response.status} ${errorText}`);
  }
}

export const useModelEntities = (projectId: UUID) => {
  const {data: session} = useSession();
  const {data, error, isLoading, mutate: mutateModelEntities} = useSWR(session ? ["models-instantiated", projectId] : null, () => fetchModelEntities(session ? session.APIToken.accessToken : "", projectId));

  const { trigger: deleteModelEntity } = useSWRMutation(
    session ? ["models-instantiated", projectId] : null,
    async (_, { arg }: { arg: { modelInstantiatedId: UUID } }) => {
      await deleteModelEntityEndpoint(session ? session.APIToken.accessToken : "", arg.modelInstantiatedId);
      await mutateModelEntities();
      await mutate(["projects"]);
    }
  );

  return {
    modelsInstantiated: data,
    isLoading,
    isError: error,
    deleteModelEntity,
  };
}; 

export const useModelEntity = (projectId: UUID, modelInstantiatedId: UUID) => {
  const { modelsInstantiated: models } = useModelEntities(projectId);

  const modelInstantiated = useMemo(() => models?.find(modelInstantiated => modelInstantiated.id === modelInstantiatedId), [models, modelInstantiatedId]);

  return {
    modelInstantiated,
  };
};
