import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { ResultTable } from "@/types/analysis";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

async function fetchTable(
  token: string,
  projectId: UUID,
  tablePath: string
): Promise<ResultTable> {

  const response = await fetch(`${PROJECT_SERVER_URL}/table/get-table`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      project_id: projectId,
      table_path: tablePath,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch table: ${response.status} ${errorText}`);
  }

  return await response.json();
}

export function useTable(
  projectId: UUID,
  tablePath: string
) {
  const { data: session } = useSession();

  const { data: table, error, isLoading } = useSWR(
    session ? ["table", projectId, tablePath] : null,
    () => fetchTable(session!.APIToken.accessToken, projectId, tablePath)
  );

  return {
    table,
    isLoading,
    isError: error,
  };
}

