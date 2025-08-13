import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { DataSource, FileDataSource } from '@/types/data-sources';

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

  return response.json();
}

async function createFileDataSource(token: string, files: File[]): Promise<FileDataSource> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await fetch(`${API_URL}/data-sources/file-data-sources`, {
    // FormData post with files
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

  return response.json();
}


export const useDataSources = () => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(session ? "data-sources" : null, () => fetchDataSources(session ? session.APIToken.accessToken : ""));

  const { trigger: triggerCreateFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { files: File[] } }) => {
      const newDataSource = await createFileDataSource(session ? session.APIToken.accessToken : "", arg.files);
      return [...(dataSources || []), newDataSource];
    }
  );

  return { dataSources, mutateDataSources, error, isLoading, triggerCreateFileDataSource };
}