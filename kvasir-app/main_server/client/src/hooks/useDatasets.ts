import useSWR from "swr";
import { useSession } from "next-auth/react";
import { snakeToCamelKeys } from "@/lib/utils";
import { UUID } from "crypto";
import { Dataset, ObjectGroupWithObjects } from "@/types/ontology/dataset";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchDataset(token: string, datasetId: UUID): Promise<Dataset> {
  const response = await fetch(`${API_URL}/data-objects/dataset/${datasetId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch dataset', errorText);
    throw new Error(`Failed to fetch dataset: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchDatasetsByIds(token: string, datasetIds: UUID[]): Promise<Dataset[]> {
  const params = new URLSearchParams();
  datasetIds.forEach(id => params.append('dataset_ids', id));

  const response = await fetch(`${API_URL}/data-objects/datasets-by-ids?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch datasets by ids', errorText);
    throw new Error(`Failed to fetch datasets by ids: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchObjectGroupsInDataset(token: string, datasetId: UUID): Promise<ObjectGroupWithObjects[]> {
  const response = await fetch(`${API_URL}/data-objects/object-groups-in-dataset/${datasetId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch object groups in dataset', errorText);
    throw new Error(`Failed to fetch object groups in dataset: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


export const useDatasetsByIds = (datasetIds?: UUID[]) => {
  const { data: session } = useSession();
  const { data: datasets, mutate: mutateDatasets, error, isLoading } = useSWR(
    session && datasetIds && datasetIds.length > 0 ? ["datasets-by-ids", datasetIds] : null,
    () => fetchDatasetsByIds(session ? session.APIToken.accessToken : "", datasetIds || [])
  );

  return {
    datasets,
    mutateDatasets,
    isLoading,
    isError: error,
  };
}; 

export const useDataset = (datasetId?: UUID) => {
  const { data: session } = useSession();
  const { data: dataset, mutate: mutateDataset, error, isLoading } = useSWR(
    session && datasetId ? ["dataset", datasetId] : null,
    () => fetchDataset(session ? session.APIToken.accessToken : "", datasetId!)
  );

  const { data: objectGroups, mutate: mutateObjectGroups } = useSWR(
    session && datasetId ? ["object-groups", datasetId] : null,
    () => fetchObjectGroupsInDataset(session ? session.APIToken.accessToken : "", datasetId!)
  );

  return {
    dataset,
    objectGroups,
    mutateDataset,
    mutateObjectGroups,
    isLoading,
    isError: error,
  };
};


