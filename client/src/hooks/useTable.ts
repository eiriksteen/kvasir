import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface ResultTable {
  data: Record<string, unknown[]>;
  indexColumn: string;
}

async function fetchTableData(
  token: string,
  tableId: UUID,
  mountNodeId: UUID
): Promise<ResultTable> {
  const response = await fetch(
    `${API_URL}/visualization/tables/${tableId}/download?mount_node_id=${mountNodeId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch table data: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export function useTable(tableId: UUID, mountNodeId: UUID) {
  const { data: session } = useSession();

  const { data: tableData, error, isLoading } = useSWR(
      session && tableId && mountNodeId ? ["table-data", tableId, mountNodeId] : null,
    () => fetchTableData(session!.APIToken.accessToken, tableId, mountNodeId)
  );

  return {
    tableData,
    isLoading,
    isError: error,
  };
}
