import useSWR from "swr";
import { fetchDatasets, fetchObjectGroupsInDataset } from "@/lib/api";
import { useSession } from "next-auth/react";
import { useMemo } from "react";

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