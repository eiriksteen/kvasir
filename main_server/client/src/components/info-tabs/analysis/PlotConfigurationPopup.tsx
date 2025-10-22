'use client';

import { useState, useEffect } from 'react';
import { usePlots } from '@/hooks/usePlots';
import { UUID } from 'crypto';
import { BasePlot } from '@/types/plots';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import { PlotColumn, PlotConfig, PREDEFINED_COLORS, StraightLine, MarkArea } from '@/types/plots';
import { Plus, Trash2 } from 'lucide-react';

interface PlotConfigurationPopupProps {
    isOpen: boolean;
    onClose: () => void;
    availableColumns: string[];
    analysisResultId: UUID;
    plot?: BasePlot;
}

const LINE_TYPES = [
    { value: 'line', label: 'Line' },
    { value: 'bar', label: 'Bar' },
    { value: 'scatter', label: 'Scatter' }
];

export default function PlotConfigurationPopup({ isOpen, onClose, availableColumns, analysisResultId, plot }: PlotConfigurationPopupProps) {
    const [activeTab, setActiveTab] = useState<'data' | 'metadata' | 'advanced'>('data');
    const [title, setTitle] = useState('');
    const [subtitle, setSubtitle] = useState('');
    const [plotColumns, setPlotColumns] = useState<PlotColumn[]>([]);
    const [xAxisColumn, setXAxisColumn] = useState<PlotColumn>();
    const [yAxisColumns, setYAxisColumns] = useState<PlotColumn[]>([]);
    const [yAxisMin, setYAxisMin] = useState('');
    const [yAxisMax, setYAxisMax] = useState('');
    const [yAxisAuto, setYAxisAuto] = useState(true);
    const [yAxisName, setYAxisName] = useState('');
    const [xAxisName, setXAxisName] = useState('');
    const [yAxisUnits, setYAxisUnits] = useState('');
    const [xAxisUnits, setXAxisUnits] = useState('');
    const [yAxis2Enabled, setYAxis2Enabled] = useState(false);
    const [yAxis2Auto, setYAxis2Auto] = useState(true);
    const [yAxis2Min, setYAxis2Min] = useState('');
    const [yAxis2Max, setYAxis2Max] = useState('');
    const [yAxis2Name, setYAxis2Name] = useState('');
    const [yAxis2Units, setYAxis2Units] = useState('');
    const [selectAll, setSelectAll] = useState(false);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    
    // Advanced options state
    const [straightLines, setStraightLines] = useState<StraightLine[]>([]);
    const [markAreas, setMarkAreas] = useState<MarkArea[]>([]);
    const [sliderEnabled, setSliderEnabled] = useState(false);
    const { createPlot, updatePlot, deletePlot } = usePlots(analysisResultId);

    useEffect(() => {
        if (availableColumns.length > 0) {
            const newPlotColumns = availableColumns.map((column, index) => ({
                name: column,
                lineType: 'line' as const,
                color: PREDEFINED_COLORS[index % PREDEFINED_COLORS.length],
                enabled: true,
                yAxisIndex: 0
            }));
            setPlotColumns(newPlotColumns);
            
            // Set initial X-axis and Y-axis columns directly
            const initialXAxisColumn = newPlotColumns[0];
            const initialYColumns = newPlotColumns.slice(1);
            setXAxisColumn(initialXAxisColumn);
            setYAxisColumns(initialYColumns);
        }
    }, [availableColumns]);

    // Populate form fields when editing an existing plot
    useEffect(() => {
        if (plot && plot.plotConfig) {
            const config = plot.plotConfig;
            setTitle(config.title || '');
            setSubtitle(config.subtitle || '');
            setXAxisColumn(config.xAxisColumn || availableColumns[0] || '');
            
            if (config.yAxisColumns) {
                setYAxisColumns(config.yAxisColumns);
            }
            
            setYAxisAuto(config.yAxisAuto);
            setYAxisMin(config.yAxisMin?.toString() || '');
            setYAxisMax(config.yAxisMax?.toString() || '');
            setYAxisName(config.yAxisName || '');
            setXAxisName(config.xAxisName || '');
            setYAxisUnits(config.yAxisUnits || '');
            setXAxisUnits(config.xAxisUnits || '');
            setYAxis2Enabled(config.yAxis2Enabled || false);
            setYAxis2Auto(config.yAxis2Auto !== undefined ? config.yAxis2Auto : true);
            setYAxis2Min(config.yAxis2Min?.toString() || '');
            setYAxis2Max(config.yAxis2Max?.toString() || '');
            setYAxis2Name(config.yAxis2Name || '');
            setYAxis2Units(config.yAxis2Units || '');
            
            // Load advanced options if they exist
            setStraightLines(config.straightLines || []);
            setMarkAreas(config.markAreas || []);
            setSliderEnabled(config.sliderEnabled || false);
        }
    }, [plot, availableColumns]);

    const handleConfirm = () => {
        const enabledColumns = yAxisColumns.filter(col => col.enabled);
        
        const plotConfig: PlotConfig = {
            title: title,
            subtitle: subtitle,
            xAxisColumn: xAxisColumn as PlotColumn,
            yAxisColumns: yAxisColumns,
            yAxisAuto: yAxisAuto,
            yAxisMin: yAxisAuto ? null : parseFloat(yAxisMin) || null,
            yAxisMax: yAxisAuto ? null : parseFloat(yAxisMax) || null,
            yAxisName: yAxisName || null,
            xAxisName: xAxisName || null,
            yAxisUnits: yAxisUnits || null,
            xAxisUnits: xAxisUnits || null,
            yAxis2Enabled: yAxis2Enabled,
            yAxis2Auto: yAxis2Enabled ? yAxis2Auto : true,
            yAxis2Min: yAxis2Enabled && !yAxis2Auto ? (parseFloat(yAxis2Min) || null) : null,
            yAxis2Max: yAxis2Enabled && !yAxis2Auto ? (parseFloat(yAxis2Max) || null) : null,
            yAxis2Name: yAxis2Enabled ? (yAxis2Name || null) : null,
            yAxis2Units: yAxis2Enabled ? (yAxis2Units || null) : null,
            // Advanced options
            straightLines: straightLines.length > 0 ? straightLines : undefined,
            markAreas: markAreas.length > 0 ? markAreas : undefined,
            sliderEnabled: sliderEnabled,
        };
        
        if (plot) {
            updatePlot({
                plotId: plot.id,
                plotUpdate: {
                    plotConfig: plotConfig
                }
            });
        } else {
            createPlot({
                plotCreate: {
                    analysisResultId: analysisResultId,
                    plotConfig: plotConfig
                }
            });
        }
        onClose();
    };

    const toggleColumn = (columnName: string) => {
        const newColumns = yAxisColumns.map(col => 
            col.name === columnName ? { ...col, enabled: !col.enabled } : col
        );
        setYAxisColumns(newColumns);
    };

    const updateColumnProperty = (columnName: string, property: keyof PlotColumn, value: string | number) => {
        const newColumns = yAxisColumns.map(col => 
            col.name === columnName ? { ...col, [property]: value } : col
        );
        setYAxisColumns(newColumns);
    };

    const handleXAxisChange = (newXAxisColumnName: string) => {
        const newXAxisColumn = plotColumns.find(col => col.name === newXAxisColumnName);
        
        if (!newXAxisColumn) {
            console.error("Could not find column with name:", newXAxisColumnName);
            return;
        }
        
        setXAxisColumn(newXAxisColumn);
        
        const newYColumns = plotColumns.filter(col => 
            col.name !== newXAxisColumnName
        );
        setYAxisColumns(newYColumns);
    };

    const selectAllColumns = () => {
        if (selectAll) {
            setYAxisColumns(prev => prev.map(col => ({ ...col, enabled: true })));
        } else {
            setYAxisColumns(prev => prev.map(col => ({ ...col, enabled: false })));
        }
        setSelectAll(!selectAll);
    };

    const handleDeletePlot = () => {
        setShowDeleteConfirmation(true);
    };

    const confirmDeletePlot = () => {
        if (plot) {
            deletePlot({
                plotId: plot.id
            });
            setShowDeleteConfirmation(false);
            onClose();
        }
    };

    const cancelDeletePlot = () => {
        setShowDeleteConfirmation(false);
    };

    // Helper functions for managing straight lines and mark areas
    const addStraightLine = () => {
            setStraightLines([...straightLines, { 
            yValue: null, 
            color: PREDEFINED_COLORS[straightLines.length % PREDEFINED_COLORS.length],
            name: 'New Line',
            includeInLegend: true
        }]);
    };

    const removeStraightLine = (index: number) => {
        setStraightLines(straightLines.filter((_, i) => i !== index));
    };

    const updateStraightLine = (index: number, field: keyof StraightLine, value: string | number | boolean) => {
        const newLines = [...straightLines];
        newLines[index] = { ...newLines[index], [field]: value };
        setStraightLines(newLines);
    };

    const addMarkArea = () => {
        setMarkAreas([...markAreas, { 
            name: `Area ${markAreas.length + 1}`,
            color: PREDEFINED_COLORS[markAreas.length % PREDEFINED_COLORS.length],
            includeInLegend: true,
            yStart: null, 
            yEnd: null, 
            xStart: null, 
            xEnd: null 
        }]);
    };

    const removeMarkArea = (index: number) => {
        setMarkAreas(markAreas.filter((_, i) => i !== index));
    };

    const updateMarkArea = (index: number, field: keyof MarkArea, value: string | number | boolean | null) => {
        const newAreas = [...markAreas];
        newAreas[index] = { ...newAreas[index], [field]: value };
        setMarkAreas(newAreas);
    };


    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 w-[700px] max-w-[95vw] max-h-[90vh] overflow-y-auto border border-gray-300">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Configure Plot</h3>
                
                {/* Tab Navigation */}
                <div className="flex border-b border-gray-300 mb-6">
                    <button
                        onClick={() => setActiveTab('data')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'data'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Data
                    </button>
                    <button
                        onClick={() => setActiveTab('metadata')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'metadata'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Metadata
                    </button>
                    <button
                        onClick={() => setActiveTab('advanced')}
                        className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'advanced'
                                ? 'text-[#0E4F70] border-b-2 border-[#0E4F70]'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Advanced
                    </button>
                </div>

                <div className="space-y-6">
                    {activeTab === 'metadata' && (
                        <div className="space-y-6">
                            {/* Title and Subtitle */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Plot Title
                                </label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                    placeholder="Enter plot title"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Subtitle
                                </label>
                                <input
                                    type="text"
                                    value={subtitle}
                                    onChange={(e) => setSubtitle(e.target.value)}
                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                    placeholder="Enter subtitle (optional)"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'data' && (
                        <div className="space-y-6">
                            {/* X-Axis Column */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    X-Axis Column
                                </label>
                                <select
                                    value={xAxisColumn?.name}
                                    onChange={(e) => handleXAxisChange(e.target.value)}
                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                >
                                    {availableColumns.map((column) => (
                                        <option key={column} value={column}>
                                            {column}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Axis Names and Units */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        X-Axis Name
                                    </label>
                                    <input
                                        type="text"
                                        value={xAxisName}
                                        onChange={(e) => setXAxisName(e.target.value)}
                                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                        placeholder="X-axis label"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        X-Axis Units
                                    </label>
                                    <input
                                        type="text"
                                        value={xAxisUnits}
                                        onChange={(e) => setXAxisUnits(e.target.value)}
                                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                        placeholder="Units (e.g., days, months)"
                                    />
                                </div>
                            </div>

                            {/* Y-Axis Columns */}
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <label className="block text-sm font-medium text-zinc-300">
                                        Y-Axis Columns
                                    </label>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={selectAllColumns}
                                            className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                        >
                                            {selectAll? "Select All" : "Deselect All"}
                                        </button>
                                    </div>
                                </div>
                                
                                <div className="space-y-3 max-h-48 overflow-y-auto">
                                    {yAxisColumns.map((column: PlotColumn) => (
                                        <div key={column.name} className="flex items-center gap-3 p-3 bg-gray-100 rounded border border-gray-300">
                                            <input
                                                type="checkbox"
                                                checked={column.enabled}
                                                onChange={() => toggleColumn(column.name)}
                                                className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                            />
                                            
                                            <span className="text-sm text-gray-900 min-w-[100px]">{column.name}</span>
                                            
                                            <select
                                                value={column.lineType}
                                                onChange={(e) => updateColumnProperty(column.name, 'lineType', e.target.value)}
                                                className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 text-sm focus:outline-none focus:ring-1 focus:ring-[#0E4F70]"
                                            >
                                                {LINE_TYPES.map(type => (
                                                    <option key={type.value} value={type.value}>
                                                        {type.label}
                                                    </option>
                                                ))}
                                            </select>
                                            
                                            <input
                                                type="color"
                                                value={column.color}
                                                onChange={(e) => updateColumnProperty(column.name, 'color', e.target.value)}
                                                className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                                            />

                                            {yAxis2Enabled && (
                                                <select
                                                    value={column.yAxisIndex}
                                                    onChange={(e) => updateColumnProperty(column.name, 'yAxisIndex', parseInt(e.target.value))}
                                                    className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 text-sm focus:outline-none focus:ring-1 focus:ring-[#0E4F70]"
                                                >
                                                    <option value={0}>Y-Axis 1</option>
                                                    <option value={1}>Y-Axis 2</option>
                                                </select>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Y-Axis 1 Configuration */}
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-3">
                                    Y-Axis 1 Configuration
                                </label>
                                
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Y-Axis 1 Name
                                        </label>
                                        <input
                                            type="text"
                                            value={yAxisName}
                                            onChange={(e) => setYAxisName(e.target.value)}
                                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                            placeholder="Y-axis 1 label"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Y-Axis 1 Units
                                        </label>
                                        <input
                                            type="text"
                                            value={yAxisUnits}
                                            onChange={(e) => setYAxisUnits(e.target.value)}
                                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                            placeholder="Units (e.g., °C, $, %)"
                                        />
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-3 mb-3">
                                    <input
                                        type="checkbox"
                                        checked={yAxisAuto}
                                        onChange={(e) => setYAxisAuto(e.target.checked)}
                                        className="w-4 h-4 text-purple-600 bg-[#1a1625] border-[#271a30] rounded focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-gray-700">Automatic range</span>
                                </div>
                                
                                {!yAxisAuto && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs text-gray-600 mb-1">Minimum</label>
                                            <input
                                                type="number"
                                                value={yAxisMin}
                                                onChange={(e) => setYAxisMin(e.target.value)}
                                                className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                placeholder="Min value"
                                                step="any"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-gray-600 mb-1">Maximum</label>
                                            <input
                                                type="number"
                                                value={yAxisMax}
                                                onChange={(e) => setYAxisMax(e.target.value)}
                                                className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                placeholder="Max value"
                                                step="any"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Y-Axis 2 Configuration */}
                            <div>
                                <div className="flex items-center gap-3 mb-3">
                                    <input
                                        type="checkbox"
                                        checked={yAxis2Enabled}
                                        onChange={(e) => setYAxis2Enabled(e.target.checked)}
                                        className="w-4 h-4 text-purple-600 bg-[#1a1625] border-[#271a30] rounded focus:ring-purple-500"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Enable Second Y-Axis</span>
                                </div>
                                
                                {yAxis2Enabled && (
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    Y-Axis 2 Name
                                                </label>
                                                <input
                                                    type="text"
                                                    value={yAxis2Name}
                                                    onChange={(e) => setYAxis2Name(e.target.value)}
                                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                    placeholder="Y-axis 2 label"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                                    Y-Axis 2 Units
                                                </label>
                                                <input
                                                    type="text"
                                                    value={yAxis2Units}
                                                    onChange={(e) => setYAxis2Units(e.target.value)}
                                                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                    placeholder="Units (e.g., °C, $, %)"
                                                />
                                            </div>
                                        </div>
                                        
                                        <div className="flex items-center gap-3 mb-3">
                                            <input
                                                type="checkbox"
                                                checked={yAxis2Auto}
                                                onChange={(e) => setYAxis2Auto(e.target.checked)}
                                                className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                            />
                                            <span className="text-sm text-gray-700">Automatic range</span>
                                        </div>
                                        
                                        {!yAxis2Auto && (
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-xs text-zinc-400 mb-1">Y-Axis 2 Minimum</label>
                                                    <input
                                                        type="number"
                                                        value={yAxis2Min}
                                                        onChange={(e) => setYAxis2Min(e.target.value)}
                                                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                        placeholder="Min value"
                                                        step="any"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs text-zinc-400 mb-1">Y-Axis 2 Maximum</label>
                                                    <input
                                                        type="number"
                                                        value={yAxis2Max}
                                                        onChange={(e) => setYAxis2Max(e.target.value)}
                                                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
                                                        placeholder="Max value"
                                                        step="any"
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'advanced' && (
                        <div className="space-y-6">
                            {/* Straight Lines */}
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm font-medium text-zinc-300">Straight Lines</span>
                                    <button
                                        onClick={addStraightLine}
                                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                    >
                                        <Plus size={12} />
                                    </button>
                                </div>
                                
                                {straightLines.length > 0 && (
                                    <div className="space-y-4">
                                        {straightLines.map((line, index) => (
                                            <div key={index} className="p-4 bg-[#1a1625] rounded border border-[#271a30]">
                                                <div className="space-y-3">
                                                    <div className="grid grid-cols-16 gap-3 items-center ">
                                                        <div className="col-span-9">
                                                            <input
                                                                type="text"
                                                                value={line.name}
                                                                onChange={(e) => updateStraightLine(index, 'name', e.target.value)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="Line name"
                                                            />
                                                        </div>
                                                        <div className="col-span-4">
                                                            <input
                                                                type="number"
                                                                value={line.yValue || ''}
                                                                onChange={(e) => updateStraightLine(index, 'yValue', parseFloat(e.target.value))}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="Y-value"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <input
                                                                type="color"
                                                                value={line.color}
                                                                onChange={(e) => updateStraightLine(index, 'color', e.target.value)}
                                                                className="w-6 h-6 border border-[#271a30] rounded cursor-pointer"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <input
                                                                type="checkbox"
                                                                checked={line.includeInLegend}
                                                                onChange={(e) => updateStraightLine(index, 'includeInLegend', e.target.checked)}
                                                                className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                                                title="Include in legend"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <button
                                                                onClick={() => removeStraightLine(index)}
                                                                className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                                                            >
                                                                <Trash2 size={12} />
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Mark Areas */}
                            <div>
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm font-medium text-zinc-300">Mark Areas</span>
                                    <button
                                        onClick={addMarkArea}
                                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                    >
                                        <Plus size={12} />
                                    </button>
                                </div>
                                
                                {markAreas.length > 0 && (
                                    <div className="space-y-4">
                                        {markAreas.map((area, index) => (
                                            <div key={index} className="p-4 bg-[#1a1625] rounded border border-[#271a30]">
                                                <div className="space-y-3">
                                                    <div className="grid grid-cols-16 grid-rows-2 gap-3 items-center">
                                                        <div className="col-span-13">
                                                            <input
                                                                type="text"
                                                                value={area.name}
                                                                onChange={(e) => updateMarkArea(index, 'name', e.target.value)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="Area name"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <input
                                                                type="color"
                                                                value={area.color}
                                                                onChange={(e) => updateMarkArea(index, 'color', e.target.value)}
                                                                className="w-6 h-6 border border-[#271a30] rounded cursor-pointer"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <input
                                                                type="checkbox"
                                                                checked={area.includeInLegend}
                                                                onChange={(e) => updateMarkArea(index, 'includeInLegend', e.target.checked)}
                                                                className="w-4 h-4 text-[#0E4F70] bg-white border-gray-300 rounded focus:ring-[#0E4F70]"
                                                                title="Include in legend"
                                                            />
                                                        </div>
                                                        <div className="col-span-1">
                                                            <button
                                                                onClick={() => removeMarkArea(index)}
                                                                className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                                                            >
                                                                <Trash2 size={12} />
                                                            </button>
                                                        </div>
                                                        <div className="col-span-4">
                                                            <input
                                                                type="number"
                                                                value={area.yStart || ''}
                                                                onChange={(e) => updateMarkArea(index, 'yStart', parseFloat(e.target.value) || null)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="Y start"
                                                                step="any"
                                                            />
                                                        </div>
                                                        <div className="col-span-4">
                                                            <input
                                                                type="number"
                                                                value={area.yEnd || ''}
                                                                onChange={(e) => updateMarkArea(index, 'yEnd', parseFloat(e.target.value) || null)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="Y end"
                                                                step="any"
                                                            />
                                                        </div>
                                                        <div className="col-span-4">
                                                            <input
                                                                type="number"
                                                                value={area.xStart || ''}
                                                                onChange={(e) => updateMarkArea(index, 'xStart', parseFloat(e.target.value) || null)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="X start"
                                                                step="any"
                                                            />
                                                        </div>
                                                        <div className="col-span-4">
                                                            <input
                                                                type="number"
                                                                value={area.xEnd || ''}
                                                                onChange={(e) => updateMarkArea(index, 'xEnd', parseFloat(e.target.value) || null)}
                                                                className="w-full bg-[#0a101c] border border-[#271a30] rounded px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                                                placeholder="X end"
                                                                step="any"
                                                            />
                                                        </div>
                                                        
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Slider Option */}
                            <div>
                                <div className="flex items-center gap-3 mb-3">
                                    <input
                                        type="checkbox"
                                        checked={sliderEnabled}
                                        onChange={(e) => setSliderEnabled(e.target.checked)}
                                        className="w-4 h-4 text-purple-600 bg-[#1a1625] border-[#271a30] rounded focus:ring-purple-500"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Add Slider</span>
                                </div>
                                <p className="text-xs text-gray-500 ml-7">Add a slider control for interactive data exploration</p>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-gray-300">
                    {plot && (
                    <button
                        onClick={handleDeletePlot}
                        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            Delete Plot
                        </button>
                    )}
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={!xAxisColumn || yAxisColumns.filter(col => col.enabled).length === 0}
                        className="px-4 py-2 bg-[#0E4F70] text-white rounded hover:bg-[#0E4F70]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {plot ? 'Update Plot' : 'Create Plot'}
                    </button>
                </div>
            </div>
            
            <ConfirmationPopup
                message="Are you sure you want to delete this plot? This action cannot be undone."
                onConfirm={confirmDeletePlot}
                onCancel={cancelDeletePlot}
                isOpen={showDeleteConfirmation}
            />
        </div>
    );
}