import React, { useState, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { useDataObjectRawData } from "@/hooks/useDatasets";
import { GetRawDataRequest } from "@/types/data-objects";
import { ChevronDown, ChevronUp } from "lucide-react";

interface TimeSeriesChartProps {
  request: GetRawDataRequest;
}

const TimeSeriesChart = ({ request }: TimeSeriesChartProps) => {
  const { dataObjectRawData, isLoading, isError } = useDataObjectRawData(request);
  
  // Track which features are selected (initially only the first one)
  const allFeatures = useMemo(() => {
    if (!dataObjectRawData) return [];
    return Object.keys(dataObjectRawData.data.data);
  }, [dataObjectRawData]);

  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [isLegendExpanded, setIsLegendExpanded] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Initialize with first feature when data loads
  React.useEffect(() => {
    if (!hasInitialized && allFeatures.length > 0) {
      setSelectedFeatures([allFeatures[0]]);
      setHasInitialized(true);
    }
  }, [allFeatures, hasInitialized]);

  // Determine which features to show in collapsed view (max 5)
  const visibleFeatures = useMemo(() => {
    if (allFeatures.length <= 7) return allFeatures;
    
    // Always include selected features
    const visible = new Set(selectedFeatures);
    
    // Fill up to 5 with features from the start
    for (const feature of allFeatures) {
      if (visible.size >= 7) break;
      visible.add(feature);
    }
    
    return Array.from(visible);
  }, [allFeatures, selectedFeatures]);

  const toggleFeature = (feature: string) => {
    setSelectedFeatures((prev) =>
      prev.includes(feature)
        ? prev.filter((f) => f !== feature)
        : [...prev, feature]
    );
  };

  // Generate colors for features (using ECharts default color palette)
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
  ];
  
  const getFeatureColor = (feature: string) => {
    const index = allFeatures.indexOf(feature);
    return colors[index % colors.length];
  };


  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center text-zinc-500">
        Loading time series data...
      </div>
    );
  }

  if (isError || !dataObjectRawData) {
    return (
      <div className="w-full h-full flex items-center justify-center text-red-500">
        Failed to load time series data
      </div>
    );
  }

  // Get the first feature's timestamps for x-axis
  const firstFeatureName = Object.keys(dataObjectRawData.data.data)[0];
  const timestamps = dataObjectRawData.data.data[firstFeatureName]?.map(([timestamp]) => timestamp) || [];

  // ECharts configuration
  const options = {
    backgroundColor: "transparent",
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
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: "10px",
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
      scale: true,
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
    series: Object.keys(dataObjectRawData.data.data).map((featureName) => ({
      name: featureName,
      type: "line",
      data: selectedFeatures.includes(featureName)
        ? dataObjectRawData.data.data[featureName]?.map(([, value]) => value) || []
        : [],
      smooth: true,
      symbol: "none",
      lineStyle: {
        width: 2,
        color: getFeatureColor(featureName),
      },
      itemStyle: {
        color: getFeatureColor(featureName),
      },
    })),
  };

  const LegendItem = ({ feature }: { feature: string }) => {
    const isSelected = selectedFeatures.includes(feature);
    const color = getFeatureColor(feature);

    return (
      <button
        onClick={() => toggleFeature(feature)}
        className="inline-flex items-center gap-1.5 px-1.5 py-0.5 cursor-pointer transition-opacity hover:opacity-70"
        style={{
          opacity: isSelected ? 1 : 0.4,
        }}
      >
        <span
          className="w-3 h-3 flex-shrink-0"
          style={{
            backgroundColor: color,
            borderRadius: "2px",
          }}
        />
        <span
          style={{
            color: "#000",
            fontSize: "12px",
            fontFamily: "sans-serif",
          }}
        >
          {feature}
        </span>
      </button>
    );
  };

  return (
    <div className="w-full h-full relative flex flex-col">
      {/* Custom Legend - Collapsed View */}
      <div className="px-3 py-2 border-b border-zinc-200 bg-white z-20">
        <div className="flex items-center gap-3 flex-wrap">
          {visibleFeatures.map((feature) => (
            <LegendItem key={feature} feature={feature} />
          ))}
          {allFeatures.length > 5 && (
            <button
              onClick={() => setIsLegendExpanded(true)}
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 cursor-pointer transition-opacity hover:opacity-70"
              style={{
                color: "#666",
                fontSize: "12px",
              }}
            >
              <span>+{allFeatures.length - visibleFeatures.length}</span>
              <ChevronDown size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Expanded Dropdown - Overlays on top of chart */}
      {isLegendExpanded && (
        <div className="absolute left-0 right-0 top-0 bg-white border-b-2 border-zinc-300 shadow-lg z-30 p-3 max-h-80 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <span style={{ fontSize: "13px", fontWeight: 500, color: "#333" }}>
              Select Features
            </span>
            <button
              onClick={() => setIsLegendExpanded(false)}
              className="cursor-pointer transition-opacity hover:opacity-70 p-0.5"
              style={{ color: "#666" }}
            >
              <ChevronUp size={16} />
            </button>
          </div>
          <div className="flex flex-wrap gap-3">
            {allFeatures.map((feature) => (
              <LegendItem key={feature} feature={feature} />
            ))}
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="flex-1">
        <ReactECharts
          option={options}
          style={{ height: "100%", width: "100%" }}
        />
      </div>
    </div>
  );
};

export default TimeSeriesChart;
