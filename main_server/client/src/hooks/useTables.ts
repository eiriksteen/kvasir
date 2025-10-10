import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation';
import { UUID } from "crypto";
import { TableUpdate, TableCreate, BaseTable } from "@/types/tables";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// routes for tables

export async function createTableEndpoint(token: string, tableCreate: TableCreate): Promise<BaseTable> {
  const response = await fetch(`${API_URL}/tables/create-table`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(tableCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create table', errorText);
    throw new Error(`Failed to create table: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function fetchTableEndpoint(token: string, tableId: string): Promise<BaseTable> {
  const response = await fetch(`${API_URL}/tables/${tableId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch table', errorText);
    throw new Error(`Failed to fetch table: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function fetchTablesByAnalysisResultEndpoint(token: string, analysisResultId: string): Promise<BaseTable[]> {
  const response = await fetch(`${API_URL}/tables/get-tables-by-analysis-result-id/${analysisResultId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch tables by analysis result', errorText);
    throw new Error(`Failed to fetch tables by analysis result: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function updateTableEndpoint(token: string, tableId: string, tableUpdate: TableUpdate): Promise<BaseTable> {
  const response = await fetch(`${API_URL}/tables/update-table/${tableId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(tableUpdate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to update table', errorText);
    throw new Error(`Failed to update table: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function deleteTableEndpoint(token: string, tableId: string): Promise<void> {
  const response = await fetch(`${API_URL}/tables/delete-table/${tableId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete table', errorText);
    throw new Error(`Failed to delete table: ${response.status} ${errorText}`);
  }
}






// Hook for managing tables for a specific analysis result
export const useTables = (analysisResultId: UUID) => {
  const { data: session } = useSession();

  const { data: tables, mutate: mutateTables } = useSWR(
    ["tables", analysisResultId], 
    () => fetchTablesByAnalysisResultEndpoint(session?.APIToken.accessToken || "", analysisResultId)
  );

  const { trigger: createTable } = useSWRMutation(
    "tables",
    async (_, { arg }: { arg: { tableCreate: TableCreate } }) => {
      const table = await createTableEndpoint(session ? session.APIToken.accessToken : "", arg.tableCreate);
      return table;
    },
    {
      populateCache: (newTable) => {
        mutateTables((current: BaseTable[] = []) => [...current, newTable]);
      }
    }
  );

  const { trigger: updateTable } = useSWRMutation(
    "tables",
    async (_, { arg }: { arg: { tableId: string, tableUpdate: TableUpdate } }) => {
      const table = await updateTableEndpoint(session ? session.APIToken.accessToken : "", arg.tableId, arg.tableUpdate);
      return table;
    },
    {
      populateCache: (updatedTable) => {
        mutateTables((current: BaseTable[] = []) => 
          current.map(table => table.id === updatedTable.id ? updatedTable : table)
        );
      }
    }
  );

  const { trigger: deleteTable } = useSWRMutation(
    "tables",
    async (_, { arg }: { arg: { tableId: string } }) => {
      await deleteTableEndpoint(session ? session.APIToken.accessToken : "", arg.tableId);
      return arg.tableId;
    },
    {
      populateCache: (deletedTableId) => {
        mutateTables((current: BaseTable[] = []) => 
          current.filter(table => table.id !== deletedTableId)
        );
      }
    }
  );

  return {
    tables,
    mutateTables,
    createTable,
    updateTable,
    deleteTable
  };
};