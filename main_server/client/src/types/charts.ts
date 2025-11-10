// TypeScript types mirroring schemas/src/synesis_schemas/project_server/charts.py

export interface XAxis {
  type: "category" | "value" | "time" | "log";
  data?: (string | number | Date)[] | null;
  name?: string | null;
  nameLocation?: "start" | "middle" | "end" | null;
}

export interface YAxis {
  type: "category" | "value" | "time" | "log";
  name?: string | null;
  nameLocation?: "start" | "middle" | "end" | null;
  min?: number | "dataMin" | null;
  max?: number | "dataMax" | null;
}

export interface LineStyle {
  color?: string | null;
  width?: number | null;
  type?: "solid" | "dashed" | "dotted";
}

export interface ItemStyle {
  color?: string | null;
}

export interface MarkLineDataItem {
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
  type?: "min" | "max" | "average" | "median" | null;
  lineStyle?: LineStyle | null;
  label?: Record<string, unknown> | null;
}

export interface MarkLine {
  silent?: boolean | null;
  symbol?: string | string[] | null;
  lineStyle?: LineStyle | null;
  data: (MarkLineDataItem | MarkLineDataItem[])[];
}

export interface MarkAreaDataItem {
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
  type?: "min" | "max" | "average" | "median" | null;
  itemStyle?: ItemStyle | null;
}

export interface MarkArea {
  silent?: boolean | null;
  itemStyle?: ItemStyle | null;
  data: [MarkAreaDataItem, MarkAreaDataItem][]; // Each item is a pair [start, end]
}

export interface VisualMapContinuous {
  type: "continuous";
  min: number;
  max: number;
  text?: string[] | null;
  inRange?: Record<string, unknown> | null;
  outOfRange?: Record<string, unknown> | null;
  orient?: "horizontal" | "vertical" | null;
  left?: string | number | null;
  right?: string | number | null;
  top?: string | number | null;
  bottom?: string | number | null;
  calculable?: boolean | null;
  seriesIndex?: number | number[] | null;
  dimension?: number | null;
}

export interface VisualMapPiecewise {
  type: "piecewise";
  pieces?: Record<string, unknown>[] | null;
  categories?: string[] | null;
  min?: number | null;
  max?: number | null;
  splitNumber?: number | null;
  text?: string[] | null;
  inRange?: Record<string, unknown> | null;
  outOfRange?: Record<string, unknown> | null;
  orient?: "horizontal" | "vertical" | null;
  left?: string | number | null;
  right?: string | number | null;
  top?: string | number | null;
  bottom?: string | number | null;
  seriesIndex?: number | number[] | null;
  dimension?: number | null;
}

export type VisualMap = VisualMapContinuous | VisualMapPiecewise;

export interface Series {
  name?: string | null;
  type: "line" | "bar" | "scatter" | "pie" | "candlestick" | "boxplot" | "heatmap";
  data: (number | number[] | Record<string, unknown>)[];
  xAxisIndex?: number | null;
  yAxisIndex?: number | null;
  smooth?: boolean | null;
  lineStyle?: LineStyle | null;
  itemStyle?: ItemStyle | null;
  markLine?: MarkLine | null;
  markArea?: MarkArea | null;
  showSymbol?: boolean | null;
  symbolSize?: number | null;
  areaStyle?: Record<string, unknown> | null;
  stack?: string | null;
}

export interface Legend {
  show?: boolean | null;
  data?: string[] | null;
  orient?: "horizontal" | "vertical" | null;
  left?: "left" | "center" | "right" | null;
  top?: "top" | "middle" | "bottom" | null;
}

export interface Grid {
  left?: string | number | null;
  right?: string | number | null;
  top?: string | number | null;
  bottom?: string | number | null;
  containLabel?: boolean | null;
}

export interface Tooltip {
  show?: boolean | null;
  trigger?: "item" | "axis" | "none" | null;
  axisPointer?: Record<string, unknown> | null;
}

export interface DataZoom {
  type: "inside" | "slider";
  xAxisIndex?: number | number[] | null;
  yAxisIndex?: number | number[] | null;
  start?: number | null;
  end?: number | null;
}

export interface EChartsOption {
  legend?: Legend | null;
  tooltip?: Tooltip | null;
  grid?: Grid | null;
  xAxis?: XAxis | XAxis[] | null;
  yAxis?: YAxis | YAxis[] | null;
  series: Series[];
  visualMap?: VisualMap | VisualMap[] | null;
  dataZoom?: DataZoom | DataZoom[] | null;
}

