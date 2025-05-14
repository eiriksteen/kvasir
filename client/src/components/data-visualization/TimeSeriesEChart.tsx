import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import { useTimeSeriesData } from "@/hooks/useTimeSeriesDataset";
import { EntityMetadata } from "@/types/datasets";
import { ChevronLeft, Plus } from "lucide-react";

interface TimeSeriesEChartProps {
  entityId: string;
  entity: EntityMetadata;
}

const TimeSeriesEChart = ({ entityId, entity }: TimeSeriesEChartProps) => {
  const { data: timeSeriesData } = useTimeSeriesData(entityId);
  const [showAllMetadata, setShowAllMetadata] = useState(false);

  if (!timeSeriesData) {
    return (
      <div className="w-full h-full flex items-center justify-center text-zinc-500">
        Loading time series data...
      </div>
    );
  }
  
  // ECharts configuration
  const options = {
    backgroundColor: 'transparent',
    title: {
      text: entity.originalId,
      left: 'center',
      top: 0,
      textStyle: {
        color: '#e5e7eb',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0a101c',
      borderColor: '#2a4170',
      textStyle: {
        color: '#e5e7eb'
      }
    },
    legend: {
      data: timeSeriesData.featureNames,
      textStyle: {
        color: '#e5e7eb'
      },
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '60px',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      axisLine: {
        lineStyle: {
          color: '#374151'
        }
      },
      axisLabel: {
        color: '#9ca3af'
      }
    },
    yAxis: {
      type: 'value',
      splitLine: {
        show: true,
        lineStyle: {
          color: '#1f2937'
        }
      },
      axisLine: {
        lineStyle: {
          color: '#374151'
        }
      },
      axisLabel: {
        color: '#9ca3af'
      }
    },
    series: timeSeriesData.featureNames.map((featureName, featureIndex) => ({
      name: featureName,
      type: 'line',
      data: timeSeriesData.timestamps.map((timestamp, timeIndex) => [
        timestamp,
        timeSeriesData.values[featureIndex][timeIndex]
      ]),
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 2
      }
    }))
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Main content area */}
      <div className="flex-1 flex gap-2 min-h-0">
        {/* Metadata panel */}
        {showAllMetadata && (
          <div className="w-[240px] bg-[#0a101c] rounded-lg p-2 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-zinc-400 font-medium">Metadata</div>
              <button
                onClick={() => setShowAllMetadata(false)}
                className="flex items-center gap-1 text-zinc-400 hover:text-zinc-300 transition-colors"
              >
                <ChevronLeft size={14} />
                <span className="text-xs">Hide</span>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto min-h-0">
              {entity.columnNames.map((name, index) => (
                <div
                  key={name}
                  className="flex flex-col bg-[#101827] rounded px-2 py-1.5 border border-[#1a2234] mb-2"
                >
                  <span className="text-[10px] text-zinc-500 font-medium truncate">{name}</span>
                  <span className="text-xs text-zinc-200 font-semibold truncate">{entity.values[index]?.toString() || 'N/A'}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chart */}
        <div className={`bg-[#0a101c] rounded-lg p-2 flex-1 min-h-0 ${showAllMetadata ? 'w-[calc(100%-240px)]' : 'w-full'}`}>
          <ReactECharts option={options} style={{ height: '100%', width: '100%' }} />
        </div>
      </div>

      {/* Bottom buttons */}
      <div className="mt-2 flex items-center gap-2">
        {!showAllMetadata && entity.columnNames.length > 3 && (
          <button
            onClick={() => setShowAllMetadata(true)}
            className="flex items-center gap-1 text-zinc-400 hover:text-zinc-300 transition-colors py-1"
          >
            <Plus size={16} />
            <span className="text-xs">Show metadata</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default TimeSeriesEChart;
