import React from "react";
import ReactECharts from "echarts-for-react";
import { UUID } from "crypto";
import { useChart } from "@/hooks";

interface EChartWrapperProps {
  projectId: UUID;
  chartScriptPath: string;
  originalObjectId?: string;
}

const EChartWrapper = ({ 
  projectId, 
  chartScriptPath, 
  originalObjectId 
}: EChartWrapperProps) => {
  const { chartOption, isLoading, isError } = useChart(
    projectId,
    chartScriptPath,
    originalObjectId
  );

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center text-zinc-500">
        Loading chart...
      </div>
    );
  }

  if (isError || !chartOption) {
    return (
      <div className="w-full h-full flex items-center justify-center text-red-500">
        Failed to load chart
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <ReactECharts
        option={chartOption}
        style={{ height: "100%", width: "100%" }}
      />
    </div>
  );
};

export default EChartWrapper;
