import { useSession } from "next-auth/react";
import useSWR from "swr";
import { UUID } from "crypto";
import { TimeSeriesWithRawData } from "@/types/data-objects";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchTimeSeriesRawData(token: string, timeSeriesId: UUID, startDate?: string, endDate?: string): Promise<TimeSeriesWithRawData> {
  const startDateParam = startDate ? `&start_date=${startDate}` : "";
  const endDateParam = endDate ? `&end_date=${endDate}` : "";
  const response = await fetch(`${API_URL}/data-objects/time-series-data/${timeSeriesId}?${startDateParam}${endDateParam}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch time series with raw data: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

type TimeSeriesDataOptions = {
    startDate?: string;
    endDate?: string;
}

export const useTimeSeriesData = (timeSeriesId: UUID, options: TimeSeriesDataOptions = {}) => {
  const { data: session } = useSession();
  const { data: timeSeriesData } = useSWR(
    session ? `time-series-data-${timeSeriesId}` : null,
    () => fetchTimeSeriesRawData(session ? session.APIToken.accessToken : "", timeSeriesId, options.startDate, options.endDate),
  );

  // TODO: Implement pagination-like fetching to vary the start and end date

  return {
    timeSeriesData
  };
};