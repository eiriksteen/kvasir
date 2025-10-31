import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { DataSource } from '@/types/data-sources';
import { useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";

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

async function createFileDataSource(token: string, projectId: UUID, file: File): Promise<DataSource> {
  const formData = new FormData();
  formData.append('file', file);
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

export const useDataSources = (projectId: UUID) => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(
    session ? ["data-sources", projectId] : null, 
    () => fetchProjectDataSources(session ? session.APIToken.accessToken : "", projectId)
  );

  const { trigger: triggerCreateFileDataSource } = useSWRMutation(
    session ? ["data-sources", projectId] : null,
    async (_, { arg }: { arg: { file: File } }) => {
      const newDataSource = await createFileDataSource(
        session ? session.APIToken.accessToken : "", 
        projectId, 
        arg.file
      );
      await mutateDataSources();
      return newDataSource;
    }
  );

  return { 
    dataSources, 
    mutateDataSources, 
    error, 
    isLoading, 
    triggerCreateFileDataSource
  };
}

export const useDataSource = (projectId: UUID, dataSourceId: UUID) => {
  const { dataSources } = useDataSources(projectId);
  const dataSource = useMemo(() => dataSources?.find(ds => ds.id === dataSourceId), [dataSources, dataSourceId]);

  return { dataSource };
}