import { useSession } from "next-auth/react";
import useSWR from "swr";
import { fetchTimeSeriesRawData } from "@/lib/api";
import { UUID } from "crypto";


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