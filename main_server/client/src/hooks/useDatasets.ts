import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import { Dataset, ObjectGroupWithObjects } from "@/types/data-objects";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { mutate } from "swr";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchDatasets(token: string, projectId: UUID): Promise<Dataset[]> {
  const response = await fetch(`${API_URL}/project/project-datasets/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch datasets', errorText);
    throw new Error(`Failed to fetch datasets: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchObjectGroupsInDataset(token: string, datasetId: string): Promise<ObjectGroupWithObjects[]> {
  const response = await fetch(`${API_URL}/data-objects/object-groups-in-dataset/${datasetId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch object group by id', errorText);
    throw new Error(`Failed to fetch object group by id: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function deleteDatasetEndpoint(token: string, datasetId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/deletion/dataset/${datasetId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete dataset', errorText);
    throw new Error(`Failed to delete dataset: ${response.status} ${errorText}`);
  }
}


export const useDatasets = (projectId: UUID) => {
  const { data: session } = useSession();
  const { data: datasets, mutate: mutateDatasets, error, isLoading } = useSWR(
    session ? ["datasets", projectId] : null, 
    () => fetchDatasets(session ? session.APIToken.accessToken : "", projectId),
    {
      // revalidateOnFocus: false,
      //revalidateOnReconnect: false,
      revalidateIfStale: false,
    }
  );

  const { trigger: deleteDataset } = useSWRMutation(
    session ? ["datasets", projectId] : null,
    async (_, { arg }: { arg: { datasetId: UUID } }) => {
      await deleteDatasetEndpoint(session ? session.APIToken.accessToken : "", arg.datasetId);
      await mutateDatasets();
      await mutate(["projects"]);
    }
  );

  return {
    datasets,
    mutateDatasets,
    isLoading,
    isError: error,
    deleteDataset,
  };
}; 


export const useDataset = (datasetId: UUID, projectId: UUID) => {
  const { data: session } = useSession();
  const { datasets } = useDatasets(projectId);

  const dataset = useMemo(() => {
    return datasets?.find((dataset) => dataset.id === datasetId);
  }, [datasets, datasetId]);

  const { data: objectGroups } = useSWR(
    dataset ? `object-groups-${datasetId}` : null,
    () => fetchObjectGroupsInDataset(session ? session.APIToken.accessToken : "", datasetId),
  );

  return {
    dataset,
    objectGroups,
  };
};


