import React from "react";
import ReactECharts from "echarts-for-react";
import { UUID } from "crypto";
import { useChart } from "@/hooks";

interface EChartWrapperProps {
  projectId: UUID;
  chartId: UUID;
  originalObjectId?: string;
}

const EChartWrapper = ({ 
  projectId, 
  chartId, 
  originalObjectId 
}: EChartWrapperProps) => {
  const { chartOption, isLoading, isError } = useChart(
    projectId,
    chartId,
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
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
};

export default EChartWrapper;
