import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import { Dataset, ObjectGroupWithObjectList } from "@/types/data-objects";
import { snakeToCamelKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchDatasets(token: string): Promise<Dataset[]> {
  const response = await fetch(`${API_URL}/data-objects/datasets?include_object_lists=0&include_features=1`, {
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

async function fetchObjectGroupsInDataset(token: string, datasetId: string): Promise<ObjectGroupWithObjectList[]> {
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


export const useDatasets = () => {
  const { data: session } = useSession();
  const { data: datasets, mutate: mutateDatasets, error, isLoading } = useSWR(
    session ? "datasets" : null, 
    () => fetchDatasets(session ? session.APIToken.accessToken : ""),
    {
      // revalidateOnFocus: false,
      //revalidateOnReconnect: false,
      revalidateIfStale: false,
    }
  );

  return {
    datasets,
    mutateDatasets,
    isLoading,
    isError: error,
  };
}; 


export const useDataset = (datasetId: string) => {
  const { data: session } = useSession();
  const { datasets } = useDatasets();

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