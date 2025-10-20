import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { DataSource } from '@/types/data-sources';
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


async function fetchProjectDataSources(token: string, projectId: UUID): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/project/project-data-sources/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch project data sources', errorText);
    throw new Error(`Failed to fetch data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


async function createTabularFileDataSource(token: string, file: File): Promise<DataSource> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/data-sources/tabular-file-data-source`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Failed to create tabular file data source', errorText);
      throw new Error(`Failed to create tabular file data source: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return snakeToCamelKeys(data);
}


async function createKeyValueFileDataSource(token: string, file: File): Promise<DataSource> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/data-sources/key-value-file-data-source`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create key value file data source', errorText);
    throw new Error(`Failed to create key value file data source: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


export const useDataSources = () => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(session ? "data-sources" : null, () => fetchDataSources(session ? session.APIToken.accessToken : ""));

  const { trigger: triggerCreateTabularFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { file: File } }) => {
      const newDataSource = await createTabularFileDataSource(session ? session.APIToken.accessToken : "", arg.file);
      return [...(dataSources || []), newDataSource];
    }
  );

  const { trigger: triggerCreateKeyValueFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { file: File } }) => {
      const newDataSource = await createKeyValueFileDataSource(session ? session.APIToken.accessToken : "", arg.file);
      return [...(dataSources || []), newDataSource];
    }
  );

  return { dataSources, mutateDataSources, error, isLoading, triggerCreateTabularFileDataSource, triggerCreateKeyValueFileDataSource   };
}


export const useProjectDataSources = (projectId: UUID) => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(session ? ["data-sources", projectId] : null, () => fetchProjectDataSources(session ? session.APIToken.accessToken : "", projectId));

    const { trigger: triggerCreateTabularFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { file: File } }) => {
      const newDataSource = await createTabularFileDataSource(session ? session.APIToken.accessToken : "", arg.file);
      return [...(dataSources || []), newDataSource];
    }
  );

  const { trigger: triggerCreateKeyValueFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { file: File } }) => {
      const newDataSource = await createKeyValueFileDataSource(session ? session.APIToken.accessToken : "", arg.file);
      return [...(dataSources || []), newDataSource];
    }
  );

  return { dataSources, mutateDataSources, error, isLoading, triggerCreateTabularFileDataSource, triggerCreateKeyValueFileDataSource };
}


export const useDataSource = (dataSourceId: UUID) => {

  const { dataSources } = useDataSources();
  const dataSource = useMemo(() => dataSources?.find(ds => ds.id === dataSourceId), [dataSources, dataSourceId]);

  return { dataSource };
}

