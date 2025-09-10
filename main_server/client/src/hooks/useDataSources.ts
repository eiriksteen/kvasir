import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { DataSourceBase, DataSource } from '@/types/data-sources';
import { useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchDataSources(token: string): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/data-sources/data-sources`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch data sources', errorText);
    throw new Error(`Failed to fetch data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createFileDataSource(token: string, files: File[]): Promise<DataSourceBase[]> {
  const results = await Promise.all(files.map(async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/data-sources/file-data-source`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Failed to create file data source', errorText);
      throw new Error(`Failed to create file data source: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return snakeToCamelKeys(data);
  }));

  return results;
}


export const useDataSources = () => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(session ? "data-sources" : null, () => fetchDataSources(session ? session.APIToken.accessToken : ""));

  const { trigger: triggerCreateFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { files: File[] } }) => {
      const newDataSources = await createFileDataSource(session ? session.APIToken.accessToken : "", arg.files);
      return [...(dataSources || []), ...newDataSources];
    }
  );

  console.log("dataSources", dataSources);

  return { dataSources, mutateDataSources, error, isLoading, triggerCreateFileDataSource };
}


export const useDataSource = (dataSourceId: UUID) => {

  const { dataSources } = useDataSources();
  const dataSource = useMemo(() => dataSources?.find(ds => ds.id === dataSourceId), [dataSources, dataSourceId]);

  return { dataSource };
}

