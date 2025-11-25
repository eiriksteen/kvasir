import { UUID } from "crypto";

// Base Models

export interface ImageBase {
  id: UUID;
  userId: UUID;
  imagePath: string;
  createdAt: string;
  updatedAt: string;
}

export interface EchartBase {
  id: UUID;
  userId: UUID;
  chartScriptPath: string;
  createdAt: string;
  updatedAt: string;
}

export interface TableBase {
  id: UUID;
  userId: UUID;
  tablePath: string;
  createdAt: string;
  updatedAt: string;
}

// Create Models

export interface ImageCreate {
  imagePath: string;
}

export interface EchartCreate {
  chartScriptPath: string;
}

export interface TableCreate {
  tablePath: string;
}

// ============================================================================
// SMALL SCHEMA (for LLM generation)
// ============================================================================
// This minimal schema is designed for LLMs to easily generate charts.
// It contains only the essential fields needed for common visualizations.

export interface XAxisSmall {
  /** Simplified X-axis - only essential fields */
  type: string; // "category", "value", "time", "log"
  data?: (string | number | Date)[] | null;
  name?: string | null;
}

export interface YAxisSmall {
  /** Simplified Y-axis - only essential fields */
  type: string; // "category", "value", "time", "log"
  name?: string | null;
}

export interface LineStyleSmall {
  /** Simplified line style */
  color?: string | null;
  width?: number | null;
  type?: string | null; // "solid", "dashed", "dotted"
}

export interface MarkLineDataItemSmall {
  /** Mark line point - for vertical/horizontal lines */
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
  type?: string | null; // "min", "max", "average", "median"
}

export interface MarkLineSmall {
  /** Mark line - for vertical/horizontal reference lines */
  data: (MarkLineDataItemSmall | MarkLineDataItemSmall[])[];
  lineStyle?: LineStyleSmall | null;
}

export interface MarkAreaDataItemSmall {
  /** Mark area boundary point */
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
}

export interface MarkAreaSmall {
  /** Mark area - for highlighting regions/intervals */
  data: [MarkAreaDataItemSmall, MarkAreaDataItemSmall][]; // Each item is [start, end]
  itemStyle?: Record<string, unknown> | null; // e.g., {"color": "rgba(0,0,255,0.1)"}
}

export interface MarkPointDataItemSmall {
  /** Mark point - for highlighting specific data points */
  name?: string | null;
  coord?: (string | number)[] | null; // [x, y]
  type?: string | null; // "min", "max", "average"
  itemStyle?: Record<string, unknown> | null;
}

export interface MarkPointSmall {
  /** Mark point configuration */
  data: MarkPointDataItemSmall[];
}

export interface SeriesSmall {
  /** Simplified series - core visualization element */
  name?: string | null;
  type: string; // "line", "bar", "scatter"
  data: (number | number[] | Record<string, unknown>)[];

  // Optional styling
  smooth?: boolean | null; // For smooth curves (line charts)
  areaStyle?: Record<string, unknown> | null; // Fill area under line

  // Marking features
  markLine?: MarkLineSmall | null;
  markArea?: MarkAreaSmall | null;
  markPoint?: MarkPointSmall | null;
}

export interface VisualMapSmall {
  /** Simplified visual map - for color mapping */
  type: string; // "continuous", "piecewise"
  min?: number | null;
  max?: number | null;
  inRange?: Record<string, unknown> | null; // e.g., {"color": ["#blue", "#red"]}
  dimension?: number | null; // Which dimension to map (0=x, 1=y, 2=z, etc.)
}

export interface DataZoomSmall {
  /** Simplified data zoom - for zooming/panning */
  type?: string; // "inside" = mouse/touch, "slider" = UI control
  start?: number | null; // Start percentage (0-100)
  end?: number | null; // End percentage (0-100)
}

export interface EChartsOptionSmall {
  /**
   * Minimal ECharts config for LLM generation.
   * Supports: time series, bar charts, scatter plots, zooming, interval marking.
   */
  xAxis: XAxisSmall | XAxisSmall[];
  yAxis: YAxisSmall | YAxisSmall[];
  series: SeriesSmall[];
  visualMap?: VisualMapSmall | VisualMapSmall[] | null;
  dataZoom?: DataZoomSmall | DataZoomSmall[] | null;
}

// ============================================================================
// FULL SCHEMA (with all fields and defaults)
// ============================================================================
// This is the complete schema that gets sent to ECharts with sensible defaults.

export type AxisType = "category" | "value" | "time" | "log";
export type NameLocation = "start" | "middle" | "end";
export type LineType = "solid" | "dashed" | "dotted";
export type MarkType = "min" | "max" | "average" | "median";
export type SeriesType = "line" | "bar" | "scatter" | "pie" | "candlestick" | "boxplot" | "heatmap";
export type LegendOrient = "horizontal" | "vertical";
export type LegendPosition = "left" | "center" | "right" | "top" | "middle" | "bottom";
export type TooltipTrigger = "item" | "axis" | "none";
export type DataZoomType = "inside" | "slider";
export type FilterMode = "filter" | "weakFilter" | "empty" | "none";

export interface XAxis {
  type: AxisType;
  data?: (string | number | Date)[] | null;
  name?: string | null;
  nameLocation?: NameLocation | null;
  nameGap?: number | null;
  nameTextStyle?: Record<string, unknown> | null;
  boundaryGap?: boolean | string[] | null;
  min?: number | "dataMin" | null;
  max?: number | "dataMax" | null;
  splitLine?: Record<string, unknown> | null;
  axisLine?: Record<string, unknown> | null;
  axisTick?: Record<string, unknown> | null;
  axisLabel?: Record<string, unknown> | null;
  [key: string]: unknown; // Allow extra fields
}

export interface YAxis {
  type: AxisType;
  name?: string | null;
  nameLocation?: NameLocation | null;
  nameGap?: number | null;
  nameTextStyle?: Record<string, unknown> | null;
  boundaryGap?: boolean | string[] | null;
  min?: number | "dataMin" | null;
  max?: number | "dataMax" | null;
  splitLine?: Record<string, unknown> | null;
  axisLine?: Record<string, unknown> | null;
  axisTick?: Record<string, unknown> | null;
  axisLabel?: Record<string, unknown> | null;
  [key: string]: unknown; // Allow extra fields
}

export interface LineStyle {
  color?: string | null;
  width?: number | null;
  type?: LineType;
  opacity?: number | null;
  [key: string]: unknown; // Allow extra fields
}

export interface ItemStyle {
  color?: string | null;
  borderColor?: string | null;
  borderWidth?: number | null;
  opacity?: number | null;
  [key: string]: unknown; // Allow extra fields
}

export interface Label {
  show?: boolean | null;
  position?: string | null;
  formatter?: string | Record<string, unknown> | null;
  color?: string | null;
  fontSize?: number | null;
  [key: string]: unknown; // Allow extra fields
}

export interface MarkLineDataItem {
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
  type?: MarkType | null;
  lineStyle?: LineStyle | null;
  label?: Label | null;
  [key: string]: unknown; // Allow extra fields
}

export interface MarkLine {
  silent?: boolean | null;
  symbol?: string | string[] | null;
  lineStyle?: LineStyle | null;
  label?: Label | null;
  data: (MarkLineDataItem | MarkLineDataItem[])[];
  [key: string]: unknown; // Allow extra fields
}

export interface MarkAreaDataItem {
  name?: string | null;
  xAxis?: string | number | null;
  yAxis?: string | number | null;
  type?: MarkType | null;
  itemStyle?: ItemStyle | null;
  label?: Label | null;
  [key: string]: unknown; // Allow extra fields
}

export interface MarkArea {
  silent?: boolean | null;
  itemStyle?: ItemStyle | null;
  label?: Label | null;
  data: [MarkAreaDataItem, MarkAreaDataItem][];
  [key: string]: unknown; // Allow extra fields
}

export interface MarkPointDataItem {
  name?: string | null;
  coord?: (string | number)[] | null;
  type?: MarkType | null;
  itemStyle?: ItemStyle | null;
  label?: Label | null;
  symbol?: string | null;
  symbolSize?: number | number[] | null;
  [key: string]: unknown; // Allow extra fields
}

export interface MarkPoint {
  symbol?: string | null;
  symbolSize?: number | number[] | null;
  label?: Label | null;
  itemStyle?: ItemStyle | null;
  data: MarkPointDataItem[];
  [key: string]: unknown; // Allow extra fields
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
  [key: string]: unknown; // Allow extra fields
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
  [key: string]: unknown; // Allow extra fields
}

export type VisualMap = VisualMapContinuous | VisualMapPiecewise;

export interface Series {
  name?: string | null;
  type: SeriesType;
  data: (number | number[] | Record<string, unknown>)[];
  xAxisIndex?: number | null;
  yAxisIndex?: number | null;
  smooth?: boolean;
  lineStyle?: LineStyle | null;
  itemStyle?: ItemStyle | null;
  areaStyle?: Record<string, unknown> | null;
  markLine?: MarkLine | null;
  markArea?: MarkArea | null;
  markPoint?: MarkPoint | null;
  showSymbol?: boolean | null;
  symbolSize?: number | null;
  stack?: string | null;
  label?: Label | null;
  emphasis?: Record<string, unknown> | null;
  [key: string]: unknown; // Allow extra fields
}

export interface Legend {
  show?: boolean;
  data?: string[] | null;
  orient?: LegendOrient;
  left?: string | number | LegendPosition;
  top?: string | number | LegendPosition;
  right?: string | number | null;
  bottom?: string | number | null;
  [key: string]: unknown; // Allow extra fields
}

export interface Tooltip {
  show?: boolean;
  trigger?: TooltipTrigger;
  axisPointer?: Record<string, unknown> | null;
  formatter?: string | Record<string, unknown> | null;
  [key: string]: unknown; // Allow extra fields
}

export interface DataZoom {
  type: DataZoomType;
  xAxisIndex?: number | number[] | null;
  yAxisIndex?: number | number[] | null;
  start?: number | null;
  end?: number | null;
  startValue?: number | string | null;
  endValue?: number | string | null;
  minSpan?: number | null;
  maxSpan?: number | null;
  filterMode?: FilterMode | null;
  [key: string]: unknown; // Allow extra fields
}

export interface Grid {
  /** Grid configuration for positioning the chart */
  left?: string | number | null;
  right?: string | number | null;
  top?: string | number | null;
  bottom?: string | number | null;
  containLabel?: boolean | null;
  [key: string]: unknown; // Allow extra fields
}

export interface EChartsOption {
  /**
   * Complete ECharts configuration with all options and sensible defaults.
   * Can be created from EChartsOptionSmall with expand_small_option().
   */
  xAxis?: XAxis | XAxis[] | null;
  yAxis?: YAxis | YAxis[] | null;
  series: Series[];
  visualMap?: VisualMap | VisualMap[] | null;
  dataZoom?: DataZoom | DataZoom[] | null;
  legend?: Legend | null;
  tooltip?: Tooltip | null;
  grid?: Grid | null;
  [key: string]: unknown; // Allow extra fields
}

