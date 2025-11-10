import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { EChartsOption } from "@/types/charts";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

async function fetchChartOption(
  token: string,
  projectId: UUID,
  chartId: UUID,
  originalObjectId?: string
): Promise<EChartsOption> {

  const response = await fetch(`${PROJECT_SERVER_URL}/chart/get-chart/${chartId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      project_id: projectId,
      chart_id: chartId,
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
  chartId: UUID,
  originalObjectId?: string
) {
  const { data: session } = useSession();

  const { data: chartOption, error, isLoading } = useSWR(
    session ? ["chart", chartId, originalObjectId] : null,
    () => fetchChartOption(session!.APIToken.accessToken, projectId, chartId, originalObjectId)
  );

  return {
    chartOption,
    isLoading,
    isError: error,
  };
}

