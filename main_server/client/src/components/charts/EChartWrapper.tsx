import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import { convertTimeStamps, formatTimeStamps, getMinMax } from "./PlottingUtils";
import { BasePlot, PlotColumn } from "@/types/plots";
import { AggregationObjectWithRawData, Column } from "@/types/data-objects";
import PlotConfigurationPopup from "@/components/info-modals/analysis/PlotConfigurationPopup";

interface ChartProps {
  plot: BasePlot;
  aggregationData: AggregationObjectWithRawData;
}

const EChartWrapper = ({ plot, aggregationData }: ChartProps) => {
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const config = plot.plotConfig;
  
  // Handle data availability check
  const hasData = aggregationData && aggregationData.data.outputData.data && aggregationData.data.outputData.data.length > 0;
  const columnsToPlot = config.yAxisColumns.filter((col: PlotColumn) => col.enabled);
  
  if (!hasData) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-600">
        No data available for plotting
      </div>
    );
  }

  const columns = aggregationData.data.outputData.data as Column[];

  // Helper function to convert data based on datatype
  // const convertDataByType = (valueType: string, rawData: Array<any>) => {
  //   if (valueType === 'datetime' && rawData.length > 0) {
  //     // Convert bigint array to Date array
  //     return rawData.map((timestamp: bigint) => new Date(Number(timestamp) / 1000000));
  //   }
  //   return rawData;
  // };

  // Get available columns from AggregationObjectWithRawData
  const availableColumns = columns.map(col => col.name);
  
  // Get the x-axis column data
  const xAxisColumn = columns.find(col => col.name === config.xAxisColumn.name);
  const xAxisData = xAxisColumn ? xAxisColumn.values : [];

  
  // Prepare series data
  const series = columnsToPlot.map((col: PlotColumn) => {
    const column = columns.find(c => c.name === col.name);
    const columnData = column ? column.values : [];

    return {
      name: col.name,
      type: col.lineType,
      yAxisIndex: col.yAxisIndex,
      showSymbol: false,
      data: Array.from(columnData),
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: col.color,
      },
    };
  });

  // Add straight lines
  if (config.straightLines && config.straightLines.length > 0) {
    config.straightLines.forEach((line, index) => {
      series.push({
        name: line.name || `Straight Line ${index + 1}`,
        type: "line",
        yAxisIndex: 0,
        showSymbol: false,
        data: Array(xAxisData.length).fill(line.yValue),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: line.color || "#e5e7eb",
        },
      });
    });
  }

  // Add mark areas
  const markAreas: any[] = [];
  if (config.markAreas && config.markAreas.length > 0) {
    config.markAreas.forEach((area, index) => {
      if ((area.yStart !== null && area.yEnd !== null) || (area.xStart !== null && area.xEnd !== null)) {
        markAreas.push({
          name: area.name || `Mark Area ${index + 1}`,
          type: "line",
          markArea: {
            data: [[
              {
                name: area.name || `Mark Area ${index + 1}`,
                itemStyle: {
                  color: area.color ? `${area.color}20` : "rgba(139, 92, 246, 0.1)", // Use area color with transparency
                },
                yAxis: area.yStart !== null ? area.yStart : undefined,
                xAxis: area.xStart !== null ? area.xStart : undefined,
              },
              {
                yAxis: area.yEnd !== null ? area.yEnd : undefined,
                xAxis: area.xEnd !== null ? area.xEnd : undefined,
              }
            ]],
          },
        });
      }
    });
  }


  const minMax = config.yAxisAuto ? getMinMax(series.filter((serie: any) => serie.yAxisIndex === 0)) : {
    min: config.yAxisMin,
    max: config.yAxisMax,
  };

  const minMax2 = config.yAxis2Auto ? getMinMax(series.filter((serie: any) => serie.yAxisIndex === 1)) : {
    min: config.yAxis2Min,
    max: config.yAxis2Max,
  };

  // ECharts configuration
  const default_options = {
    backgroundColor: "transparent",
    title: {
      text: config.title || "Bar Chart Visualization",
      left: "center",
      top: 0,
      textStyle: {
        color: "#374151",
        fontSize: 16,
        fontWeight: "bold",
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#ffffff",
      borderColor: "#d1d5db",
      textStyle: {
        color: "#374151",
      },
      formatter: function (params: Array<{ axisValue: any; color: string; seriesName: string; value: any }>) {
        let result = `<div style="color: #111827; font-weight: bold;">${params[0].axisValue}</div>`;
        params.forEach((param) => {
          result += `<div style="margin: 4px 0;">
            <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; margin-right: 8px;"></span>
            <span style="color: #374151; font-mono text-xs">${param.seriesName}: ${param.value}</span>
          </div>`;
        });
        return result;
      }
    },
    legend: {
      data: [
        ...config.yAxisColumns.filter((col: PlotColumn) => col.enabled).map((col: PlotColumn) => col.name),
        ...(config.straightLines || []).filter(line => line.includeInLegend).map(line => line.name),
        ...(config.markAreas || []).filter(area => area.includeInLegend).map(area => area.name),
      ],
      textStyle: {
        color: "#374151",
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
      name: config.xAxisName || "",
      data: xAxisData,
      splitLine: {
        show: true,
        lineStyle: {
          color: "#e5e7eb",
        },
      },
      axisLine: {
        lineStyle: {
          color: "#d1d5db",
        },
      },
      axisLabel: {
        color: "#374151",
        fontSize: 12,
        formatter: (value: any) => {
          if (xAxisData.every(item => item instanceof Date)) {
          return formatTimeStamps(value, xAxisData);
        } else {
          return value;
        }
        },
      },
    },
    yAxis: [
        {
        type: "value",
        name: config.yAxisName || "",
        splitLine: {
          show: true,
          lineStyle: {
            color: "#e5e7eb",
          },
        },
        axisLine: {
          lineStyle: {
            color: "#d1d5db",
          },
        },
        axisLabel: {
          color: "#374151",
          formatter: (value: any) => value + " " + (config.yAxisUnits || ""),
        },
        min: minMax.min,
        max: minMax.max,
      },
      ...(config.yAxis2Enabled ? [{
        type: "value",
        name: config.yAxis2Name || "",
        splitLine: {
          show: true,
          lineStyle: {
            color: "#e5e7eb",
          },
        },
        axisLine: {
          lineStyle: {
            color: "#d1d5db",
          },
        },
        axisLabel: {
          color: "#374151",
          formatter: (value: any) => value + " " + (config.yAxis2Units || ""),
        },
        min: minMax2.min,
        max: minMax2.max, 
      }] : []),
  ],
  dataZoom: config.sliderEnabled ? [
      {
        type: 'inside', 
        xAxisIndex: 0
      },
      {
        type: 'slider',
        xAxisIndex: 0,
      }
    ] : [],
  markArea: markAreas.length > 0 ? markAreas : undefined,
  // series: series,
  series: series.concat(markAreas),
  toolbox: {
    feature: {
      myTool1: { // The name can only start with my...
        show: true,
        title: "Settings",
        icon: "M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915 M 15 12 A 3 3 0 1 1 9 12 A 3 3 0 1 1 15 12",
        onclick: () => setIsConfigOpen(true),
        emphasis: {
          iconStyle: {
            borderColor: "#e5e7eb",
          }
        }
      },
        saveAsImage: {
            show: true,
            name: config.title !== "" ? config.title : "chart",
            title: "Download chart",
            emphasis: {
              iconStyle: {
                borderColor: "#e5e7eb",
              }
            }
        },
    }
}
  };

  return (
    <div className="w-full h-full relative">
      <ReactECharts option={default_options} style={{ height: "90%", width: "100%" }} />
      {config.subtitle && <p className="text-center text-sm text-gray-600 mt-2">{config.subtitle}</p>}
      
      {/* Plot Configuration Popup */}
      <PlotConfigurationPopup
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        availableColumns={availableColumns}
        analysisResultId={plot.analysisResultId}
        plot={plot}
      />
    </div>
  );
};

export default EChartWrapper;