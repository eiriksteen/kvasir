import { UUID } from 'crypto';

export const PREDEFINED_COLORS = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
];

export interface PlotColumn {
    name: string;
    lineType: 'line' | 'bar' | 'scatter';
    color: string;
    enabled: boolean;
    yAxisIndex: number;
}

export interface StraightLine {
    yValue: number | null;
    color: string;
    name: string;
    includeInLegend: boolean;
}

export interface MarkArea {
    name: string;
    color: string;
    includeInLegend: boolean;
    yStart?: number | null;
    yEnd?: number | null;
    xStart?: number | null;
    xEnd?: number | null;
}

export interface PlotConfig {
    title: string;
    subtitle: string | null;
    xAxisColumn: PlotColumn;
    yAxisColumns: PlotColumn[];
    yAxisMin: number | null;
    yAxisMax: number | null;
    yAxisAuto: boolean;
    yAxisName: string | null;
    xAxisName: string | null;
    yAxisUnits: string | null;
    xAxisUnits: string | null;
    yAxis2Enabled: boolean;
    yAxis2Min: number | null;
    yAxis2Max: number | null;
    yAxis2Name: string | null;
    yAxis2Units: string | null;
    yAxis2Auto: boolean;
    // Advanced options
    straightLines?: StraightLine[];
    markAreas?: MarkArea[];
    sliderEnabled?: boolean;
}

export interface BasePlot {
    id: UUID;
    analysisResultId: UUID;
    plotConfig: PlotConfig;
}

export interface PlotCreate {
    analysisResultId: UUID;
    plotConfig: PlotConfig;
}

export interface PlotUpdate {
    plotConfig?: PlotConfig;
}