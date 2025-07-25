import useSWR from "swr";
//import { fetchEntityMetadataAll, fetchTimeSeriesData } from "@/lib/api";
import { useSession } from "next-auth/react";
//import { useDatasets } from "./useDatasets";
//import { useMemo } from "react";

export const useTimeSeriesDatasetMetadata = (datasetId: string) => {
  // const { datasets } = useDatasets();
  // const dataset = useMemo(() => datasets?.timeSeries?.find((dataset) => dataset.id === datasetId), [datasets, datasetId]);
  return { dataset: null };
};

export const useTimeSeriesEntityMetadata = (datasetId: string) => {
  const { data: session } = useSession();
  // const { data } = useSWR(session ? ["entity-metadata", datasetId] : null, () => fetchEntityMetadataAll(session ? session.APIToken.accessToken : "", datasetId));
  return { entities: null};
};

export const useTimeSeriesDataset = (datasetId: string) => {
  const { dataset } = useTimeSeriesDatasetMetadata(datasetId);
  const { entities } = useTimeSeriesEntityMetadata(datasetId);
  return { dataset, entities };
};

export const useTimeSeriesData = (entityId: string) => {
  const { data: session } = useSession();
  // const { data } = useSWR(session ? ["time-series-data", entityId] : null, () => fetchTimeSeriesData(session ? session.APIToken.accessToken : "", entityId));
  return { data: null };
};