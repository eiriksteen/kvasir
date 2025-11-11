import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { DataSource } from '@/types/data-sources';
import { useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";
import { mutate } from "swr";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

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

async function createFileDataSource(token: string, projectId: UUID, files: File[]): Promise<DataSource[]> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('project_id', projectId);

  const response = await fetch(`${PROJECT_SERVER_URL}/data-source/file`, {
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
}

async function deleteDataSourceEndpoint(token: string, dataSourceId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/deletion/data-source/${dataSourceId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete data source', errorText);
    throw new Error(`Failed to delete data source: ${response.status} ${errorText}`);
  }
}

async function fetchAllUserDataSources(token: string): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/data-source/data-sources`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch user data sources', errorText);
    throw new Error(`Failed to fetch data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useDataSources = (projectId?: UUID) => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(
    session ? (projectId ? ["data-sources", projectId] : ["data-sources", "all"]) : null, 
    () => projectId 
      ? fetchProjectDataSources(session ? session.APIToken.accessToken : "", projectId)
      : fetchAllUserDataSources(session ? session.APIToken.accessToken : "")
  );

  const { trigger: triggerCreateFileDataSource } = useSWRMutation(
    session && projectId ? ["data-sources", projectId] : null,
    async (_, { arg }: { arg: { files: File[] } }) => {
      if (!projectId) {
        throw new Error("Cannot create data source without a project context");
      }
      const newDataSources = await createFileDataSource(
        session ? session.APIToken.accessToken : "", 
        projectId, 
        arg.files
      );
      await mutateDataSources();
      return newDataSources;
    }
  );

  const { trigger: deleteDataSource } = useSWRMutation(
    session ? (projectId ? ["data-sources", projectId] : ["data-sources", "all"]) : null,
    async (_, { arg }: { arg: { dataSourceId: UUID } }) => {
      await deleteDataSourceEndpoint(session ? session.APIToken.accessToken : "", arg.dataSourceId);
      await mutateDataSources();
      await mutate(["projects"]);
    }
  );

  return { 
    dataSources, 
    mutateDataSources, 
    error, 
    isLoading, 
    triggerCreateFileDataSource,
    deleteDataSource
  };
}

export const useDataSource = (projectId: UUID, dataSourceId: UUID) => {
  const { dataSources } = useDataSources(projectId);
  const dataSource = useMemo(() => dataSources?.find(ds => ds.id === dataSourceId), [dataSources, dataSourceId]);

  return { dataSource };
}