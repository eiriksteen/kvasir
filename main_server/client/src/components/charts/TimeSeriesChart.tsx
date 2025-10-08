import React from "react";
import ReactECharts from "echarts-for-react";
import { useTimeSeriesData } from "@/hooks/useTimeSeriesData";
import { UUID } from "crypto";

interface TimeSeriesChartProps {
  timeSeriesId: UUID;
}

const TimeSeriesChart = ({ timeSeriesId }: TimeSeriesChartProps) => {
  const { timeSeriesData } = useTimeSeriesData(timeSeriesId);

  if (!timeSeriesData) {
    return (
      <div className="w-full h-full flex items-center justify-center text-zinc-500">
        Loading time series data...
      </div>
    );
  }

  // Get the first feature's timestamps for x-axis
  const firstFeatureName = Object.keys(timeSeriesData.data)[0];
  const timestamps = timeSeriesData.data[firstFeatureName]?.map(([timestamp]) => timestamp) || [];

  // ECharts configuration
  const options = {
    backgroundColor: "transparent",
    title: {
      text: timeSeriesData.originalId,
      left: "center",
      top: 0,
      textStyle: {
        color: "#e5e7eb",
        fontSize: 16,
        fontWeight: "bold",
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0a101c",
      borderColor: "#2a4170",
      textStyle: {
        color: "#e5e7eb",
      },
      formatter: function (params: Array<{ axisValue: string; color: string; seriesName: string; value: number }>) {
        let result = `<div style="color: #e5e7eb; font-weight: bold;">${params[0].axisValue}</div>`;
        params.forEach((param) => {
          result += `<div style="margin: 4px 0;">
            <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; margin-right: 8px;"></span>
            <span style="color: #e5e7eb; font-mono text-xs">${param.seriesName}: ${param.value}</span>
          </div>`;
        });
        return result;
      }
    },
    legend: {
      data: Object.keys(timeSeriesData.features),
      textStyle: {
        color: "#000000",
      },
      top: 30,
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: "60px",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: timestamps,
      axisLine: {
        lineStyle: {
          color: "#374151",
        },
      },
      axisLabel: {
        color: "#000000",
        formatter: function (value: string) {
          // Format timestamp for display
          return new Date(value).toLocaleString();
        }
      },
    },
    yAxis: {
      type: "value",
      splitLine: {
        show: true,
        lineStyle: {
          color: "#1f2937",
        },
      },
      axisLine: {
        lineStyle: {
          color: "#374151",
        },
      },
      axisLabel: {
        color: "#000000",
      },
    },
    series: Object.keys(timeSeriesData.features).map((featureName) => ({
      name: featureName,
      type: "line",
      data: timeSeriesData.data[featureName]?.map(([, value]) => value) || [],
      smooth: true,
      symbol: "none",
      lineStyle: {
        width: 2,
      },
    })),
  };

  return (
    <div className="w-full h-full">
      <ReactECharts option={options} style={{ height: "100%", width: "100%" }} />
    </div>
  );
};

export default TimeSeriesChart;
