import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { ResultTable } from "@/types/visualization";
import { snakeToCamelKeys } from "@/lib/utils";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

async function fetchTable(
  token: string,
  tableId: UUID
): Promise<ResultTable> {

  const response = await fetch(`${PROJECT_SERVER_URL}/table/get-table/${tableId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch table: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export function useTable(tableId: UUID) {
  const { data: session } = useSession();

  const { data: table, error, isLoading } = useSWR(
    session ? ["table", tableId] : null,
    () => fetchTable(session!.APIToken.accessToken, tableId)
  );

  return {
    table,
    isLoading,
    isError: error,
  };
}

