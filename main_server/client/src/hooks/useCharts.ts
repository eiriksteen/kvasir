import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { EChartsOption } from "@/types/charts";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

async function fetchChartOption(
  token: string,
  projectId: UUID,
  scriptPath: string,
  originalObjectId?: string
): Promise<EChartsOption> {

  const response = await fetch(`${PROJECT_SERVER_URL}/chart/get-chart`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      project_id: projectId,
      script_path: scriptPath,
      original_object_id: originalObjectId || null,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch chart: ${response.status} ${errorText}`);
  }

  return await response.json();
}

export function useChart(
  projectId: UUID,
  chartScriptPath: string,
  originalObjectId?: string
) {
  const { data: session } = useSession();

  const { data: chartOption, error, isLoading } = useSWR(
    session ? ["chart", originalObjectId]
      : null,
    () => fetchChartOption(session!.APIToken.accessToken, projectId, chartScriptPath, originalObjectId)
  );

  return {
    chartOption,
    isLoading,
    isError: error,
  };
}

