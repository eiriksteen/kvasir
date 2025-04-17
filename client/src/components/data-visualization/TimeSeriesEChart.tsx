import React from "react";
import ReactECharts from "echarts-for-react";

const TimeSeriesEChart = () => {
  // Example data
  const chartData = [
    { time: "2025-04-01", series1: 10, series2: 20 },
    { time: "2025-04-02", series1: 15, series2: 25 },
    { time: "2025-04-03", series1: 20, series2: 30 },
    { time: "2025-04-04", series1: 25, series2: 35 },
    { time: "2025-04-05", series1: 30, series2: 40 },
  ];

  // ECharts configuration
  const options = {
    backgroundColor: '#ffffff',
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['Series 1', 'Series 2']
    },
    xAxis: {
      type: 'category',
      data: chartData.map(item => item.time)
    },
    yAxis: {
      type: 'value',
      splitLine: {
        show: false
      }
    },
    series: [
      {
        name: 'Series 1',
        type: 'line',
        data: chartData.map(item => item.series1)
      },
      {
        name: 'Series 2',
        type: 'line',
        data: chartData.map(item => item.series2)
      }
    ]
  };

  return (
    <div className="w-full h-full">
      <ReactECharts option={options} style={{ height: '100%', width: '100%' }} />
    </div>
  );
};

export default TimeSeriesEChart;
