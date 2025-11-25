import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation';
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { DataSource, DataSourceCreate, DataSourceDetailsCreate } from "@/types/ontology/data-source";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchDataSources(token: string): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/data-sources/data-sources`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
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

async function fetchDataSource(token: string, dataSourceId: UUID): Promise<DataSource> {
  const response = await fetch(`${API_URL}/data-sources/data-source/${dataSourceId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch data source', errorText);
    throw new Error(`Failed to fetch data source: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function fetchDataSourcesByIds(token: string, dataSourceIds: UUID[]): Promise<DataSource[]> {
  const params = new URLSearchParams();
  dataSourceIds.forEach(id => params.append('data_source_ids', id));

  const response = await fetch(`${API_URL}/data-sources/data-sources-by-ids?${params.toString()}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch data sources by ids', errorText);
    throw new Error(`Failed to fetch data sources by ids: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createDataSource(token: string, dataSourceCreate: DataSourceCreate): Promise<DataSource> {
  const response = await fetch(`${API_URL}/data-sources/data-source`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(dataSourceCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create data source', errorText);
    throw new Error(`Failed to create data source: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function addDataSourceDetails(token: string, detailsCreate: DataSourceDetailsCreate): Promise<DataSource> {
  const response = await fetch(`${API_URL}/data-sources/data-source-details`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(detailsCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to add data source details', errorText);
    throw new Error(`Failed to add data source details: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createFilesDataSources(token: string, files: File[], mountGroupId: UUID): Promise<DataSource> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('mount_group_id', mountGroupId.toString());

  const response = await fetch(`${API_URL}/data-sources/files-data-sources`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create files data sources', errorText);
    throw new Error(`Failed to create files data sources: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}
export const useDataSources = () => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(
    session ? "data-sources" : null,
    () => fetchDataSources(session ? session.APIToken.accessToken : "")
  );

  const { trigger: triggerCreateDataSource, isMutating: isCreating } = useSWRMutation(
    "data-sources",
    async (_, { arg }: { arg: DataSourceCreate }) => {
      if (!session?.APIToken?.accessToken) {
        throw new Error('No session token available');
      }
      const newDataSource = await createDataSource(
        session.APIToken.accessToken,
        arg
      );
      await mutateDataSources();
      return newDataSource;
    }
  );

  const { trigger: triggerCreateFilesDataSources, isMutating: isCreatingFiles } = useSWRMutation(
    "data-sources",
    async (_, { arg }: { arg: { files: File[]; mountGroupId: UUID } }) => {
      if (!session?.APIToken?.accessToken) {
        throw new Error('No session token available');
      }
      const newDataSource = await createFilesDataSources(session.APIToken.accessToken, arg.files, arg.mountGroupId);
      await mutateDataSources();
      return newDataSource;
    }
  );

  const { trigger: triggerAddDataSourceDetails, isMutating: isAddingDetails } = useSWRMutation(
    "data-sources",
    async (_, { arg }: { arg: DataSourceDetailsCreate }) => {
      if (!session?.APIToken?.accessToken) {
        throw new Error('No session token available');
      }
      const updatedDataSource = await addDataSourceDetails(
        session.APIToken.accessToken,
        arg
      );
      await mutateDataSources();
      return updatedDataSource;
    }
  );

  return { 
    dataSources, 
    mutateDataSources, 
    error, 
    isLoading,
    triggerCreateDataSource,
    triggerAddDataSourceDetails,
    isCreating,
    isAddingDetails,
    triggerCreateFilesDataSources,
    isCreatingFiles,
  };
};

export const useDataSourcesByIds = (dataSourceIds?: UUID[]) => {
  const { data: session } = useSession();
  const { data: dataSources, mutate: mutateDataSources, error, isLoading } = useSWR(
    session && dataSourceIds && dataSourceIds.length > 0 ? ["data-sources-by-ids", dataSourceIds] : null,
    () => fetchDataSourcesByIds(session ? session.APIToken.accessToken : "", dataSourceIds || [])
  );

  return { 
    dataSources, 
    mutateDataSources, 
    error, 
    isLoading, 
  };
};

export const useDataSource = (dataSourceId?: UUID) => {
  const { data: session } = useSession();
  const { data: dataSource, mutate: mutateDataSource, error, isLoading } = useSWR(
    session && dataSourceId ? ["data-source", dataSourceId] : null,
    () => fetchDataSource(session ? session.APIToken.accessToken : "", dataSourceId!)
  );

  return { 
    dataSource,
    mutateDataSource,
    error, 
    isLoading,
  };
};
