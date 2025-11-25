import useSWR from "swr";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// TODO: Import proper type when @/types/charts is created
type EChartsOption = Record<string, unknown>;

async function fetchChartOption(
  token: string,
  chartId: UUID,
  mountGroupId: UUID
): Promise<EChartsOption> {
  const response = await fetch(
    `${API_URL}/visualization/echarts/${chartId}/get-chart?mount_group_id=${mountGroupId}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch chart: ${response.status} ${errorText}`);
  }

  return await response.json();
}

export function useChart(
  mountGroupId: UUID,
  chartId: UUID
) {
  const { data: session } = useSession();

  const { data: chartOption, error, isLoading } = useSWR(
    session && chartId && mountGroupId ? ["chart", chartId, mountGroupId] : null,
    () => fetchChartOption(session!.APIToken.accessToken, chartId, mountGroupId)
  );

  return {
    chartOption,
    isLoading,
    isError: error,
  };
}
