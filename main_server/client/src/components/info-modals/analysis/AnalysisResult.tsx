'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { Code, Database, ChevronDown, ChevronRight, Info, Trash2, EllipsisVertical, Move, FileSearch, BarChart3, Pencil, Save, Loader2, X } from 'lucide-react';
import { AnalysisResult as AnalysisResultType, AnalysisStatusMessage } from '@/types/analysis';
import { MarkdownComponents } from '@/components/MarkdownComponents';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataSources } from '@/hooks/useDataSources';
import { useAnalysisObject } from '@/hooks/useAnalysis';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import EChartWrapper from '@/components/charts/EChartWrapper';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { UUID } from 'crypto';
import { AggregationObjectWithRawData } from '@/types/data-objects';
import { usePlots } from '@/hooks/usePlots';
import { BasePlot } from '@/types/plots';
import PlotConfigurationPopup from './PlotConfigurationPopup';
import DnDComponent from './DnDComponent';
import { useTables } from '@/hooks/useTables';
import { BaseTable } from '@/types/tables';
import TablesItem from '@/components/tables/TableItem';
import TableConfigurationPopup from '@/components/info-modals/analysis/TableConfigurationPopup';

interface AnalysisResultProps {
    projectId: UUID;
    analysisResult: AnalysisResultType;
    analysisObjectId: UUID;
}

export default function AnalysisResult({ projectId, analysisResult, analysisObjectId }: AnalysisResultProps) {
    const [showDetails, setShowDetails] = useState(false);
    const [showCode, setShowCode] = useState(false);
    const [showDatasets, setShowDatasets] = useState(false);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    const [showPlotConfiguration, setShowPlotConfiguration] = useState(false);
    const [showTableConfiguration, setShowTableConfiguration] = useState(false);
    const [showEditAnalysis, setShowEditAnalysis] = useState(false);
    const [editAnalysis, setEditAnalysis] = useState(analysisResult.analysis);
    const [isUpdating, setIsUpdating] = useState(false);
    const { datasets } = useDatasets(projectId);
    const { dataSources } = useDataSources();
    const { analysisStatusMessages, getAnalysisResultData, analysisResultData, deleteAnalysisResult, updateAnalysisResult } = useAnalysisObject(projectId, analysisObjectId);
    const [showOptions, setShowOptions] = useState(false);
    const optionsRef = useRef<HTMLDivElement>(null);
    const analysisTextareaRef = useRef<HTMLTextAreaElement>(null);
    const [isLoadingData, setIsLoadingData] = useState(false);
    const { plots } = usePlots(analysisResult.id);
    const { tables, updateTable, deleteTable } = useTables(analysisResult.id);
    
    // Handle click outside to close options
    useEffect(() => {
        if (!showOptions) return;
        
        const handleClickOutside = (event: MouseEvent) => {
            if (optionsRef.current && !optionsRef.current.contains(event.target as Node)) {
                setShowOptions(false);
            }
        };

        if (showOptions) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showOptions]);

    // Focus textarea when editing starts
    useEffect(() => {
        if (showEditAnalysis && analysisTextareaRef.current) {
            analysisTextareaRef.current.focus();
        }
    }, [showEditAnalysis]);

    // Filter streaming messages for this specific analysis result
    const streamingMessages = useMemo(() => {
        if (!analysisStatusMessages) return [];
        const filtered = analysisStatusMessages.filter((message: AnalysisStatusMessage) => 
            message.result.id === analysisResult.id
        );
        return filtered;
    }, [analysisStatusMessages, analysisResult.id]);
    

    // Get the latest streaming message for this analysis result
    const latestStreamingMessage = useMemo(() => {
        if (streamingMessages.length === 0) return null;
        return streamingMessages[streamingMessages.length - 1];
    }, [streamingMessages]);

    // Determine which content to display (streaming or static)
    const displayContent = useMemo(() => {
        if (latestStreamingMessage) {
            return latestStreamingMessage.result.analysis;
        }
        return analysisResult.analysis;
    }, [latestStreamingMessage, analysisResult.analysis]);

    // Get the most up-to-date analysis result data (either from streaming or static)
    const currentAnalysisResult = useMemo(() => {
        if (latestStreamingMessage) {
            return latestStreamingMessage.result;
        }
        return analysisResult;
    }, [latestStreamingMessage, analysisResult]);

    // Drag functionality with dnd-kit
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: analysisResult.id,
        data: {
            type: 'analysis_result',
            analysisResult: analysisResult
        }
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    // Helper function to get dataset name by ID
    const getDatasetName = (datasetId: string) => {
        if (!datasets) return `Dataset ${datasetId}`;
        
        // Check time series datasets
        const timeSeriesDataset = datasets.find((dataset: any) => dataset.id === datasetId);
        if (timeSeriesDataset) return timeSeriesDataset.name;
        
        return `Dataset ${datasetId}`;
    };

    // Helper function to get data source name by ID
    const getDataSourceName = (dataSourceId: string) => {
        if (!dataSources) return `Data Source ${dataSourceId}`;
        
        // Find the data source by ID
        const dataSource = dataSources.find((ds: any) => ds.id === dataSourceId);
        if (dataSource) return dataSource.name;
        
        return `Data Source ${dataSourceId}`;
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowDeleteConfirmation(true);
    };

    const handleConfirmDelete = async () => {
        await deleteAnalysisResult({ analysisObjectId, analysisResultId: analysisResult.id });

    };

    const handlePlot = async () => {
        try {
            setIsLoadingData(true);
            await getAnalysisResultData({ 
                analysisObjectId, 
                analysisResultId: analysisResult.id 
            });
            setShowPlotConfiguration(true);
        } catch (error) {
            console.error('Failed to get analysis result data:', error);
        } finally {
            setIsLoadingData(false);
        }
    };

    const handleTable = async () => {
        try {
            setIsLoadingData(true);
            await getAnalysisResultData({ 
                analysisObjectId, 
                analysisResultId: analysisResult.id 
            });
            setShowTableConfiguration(true);
        } catch (error) {
            console.error('Failed to get analysis result data:', error);
        } finally {
            setIsLoadingData(false);
        }
    };

    const handleUpdateAnalysis = async () => {
        if (editAnalysis.trim() && !isUpdating) {
            setIsUpdating(true);
            try {
                await updateAnalysisResult({
                    analysisResultId: analysisResult.id,
                    analysisResultUpdate: {
                        analysis: editAnalysis.trim(),
                    }
                });
                setShowEditAnalysis(false);
            } catch (error) {
                console.error('Error updating analysis result:', error);
            } finally {
                setIsUpdating(false);
            }
        }
    };

    const handleCancelEdit = () => {
        setEditAnalysis(analysisResult.analysis);
        setShowEditAnalysis(false);
    };

    // Get available columns from the analysis result data
    const availableColumns = useMemo(() => {
        const data = analysisResultData[analysisResult.id] as AggregationObjectWithRawData;
        if (data && data.data.outputData && data.data.outputData.data) {
            // Extract column names from the data array
            return data.data.outputData.data.map(col => col.name);
        }
        return [];
    }, [analysisResultData, analysisResult.id]);

    if (analysisResultData[analysisResult.id] === undefined && ((plots && plots.length > 0) || (tables && tables.length > 0))) {
        getAnalysisResultData({ 
            analysisObjectId, 
            analysisResultId: analysisResult.id 
        });
    }

    return (
        <div className="w-full">
            {/* DnD Component - positioned above the analysis result, only when not dragging */}
            {!isDragging && (
                <DnDComponent
                    nextType={"analysis_result"}
                    nextId={analysisResult.id}
                    sectionId={analysisResult.sectionId}
                />
            )}
            
            <div 
                ref={setNodeRef}
                style={style}
                {...attributes}
                className={`bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-lg py-2 px-4 mb-2 transition-opacity w-full min-w-0 ${
                    isDragging ? 'opacity-50' : 'opacity-100'
                }`}
            >   
                {isDragging ? (
                    <div className="w-full h-16 bg-[#0E4F70]/20 flex items-center justify-center rounded-lg">
                        <div className="flex items-center gap-2">
                            <FileSearch size={16} className="text-[#0E4F70] animate-pulse" />
                            <span className="text-sm text-[#0E4F70]">Moving analysis result...</span>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Main Content with Info and Delete Buttons */}
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="text-xs text-gray-700 leading-relaxed">
                                    {/* Show streaming indicator if there are streaming messages and streaming is not finished */}
                                    {streamingMessages.length > 0 && !showEditAnalysis && (
                                        <div className="mb-2 flex items-center gap-2">
                                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                            <span className="text-xs text-green-400">Streaming...</span>
                                        </div>
                                    )}
                                    {showEditAnalysis ? (
                                        <div className="space-y-3">
                                            <textarea
                                                ref={analysisTextareaRef}
                                                value={editAnalysis}
                                                onChange={(e) => setEditAnalysis(e.target.value)}
                                                className="w-full px-3 py-2 text-xs rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70] resize-none"
                                                placeholder="Edit analysis content..."
                                                rows={8}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Escape') handleCancelEdit();
                                                }}
                                                disabled={isUpdating}
                                            />
                                            <div className="flex items-center justify-evenly gap-2">
                                                <button
                                                    onClick={handleCancelEdit}
                                                    disabled={isUpdating}
                                                    className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                                >
                                                    <X size={16} />
                                                    <span>Cancel</span>
                                                </button>
                                                <button
                                                    onClick={handleUpdateAnalysis}
                                                    disabled={isUpdating || !editAnalysis.trim()}
                                                    className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                                >
                                                    {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                                                    <span>{isUpdating ? 'Saving...' : 'Save'}</span>
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={MarkdownComponents}
                                        >
                                            {displayContent}
                                        </ReactMarkdown>
                                    )}
                                </div>
                            </div>

                            <div ref={optionsRef} className="relative">
                                {showOptions && !showEditAnalysis ? (
                                    <div className="flex flex-col items-center gap-1 ml-4">
                                        <div 
                                            {...listeners}
                                            {...attributes}
                                        >
                                            <button className="p-1 text-gray-600 hover:text-gray-900 transition-colors">
                                                <Move size={12} />
                                            </button>
                                        </div>
                                        <button
                                            onClick={() => {
                                                setShowEditAnalysis(true);
                                                setShowOptions(false);
                                            }}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                                            title="Edit analysis"
                                        >
                                            <Pencil size={12} />
                                        </button>
                                        <button
                                            onClick={() => setShowDetails(!showDetails)}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                                            title="View details"
                                        >
                                            <Info size={12} />
                                        </button>
                                        <button
                                            onClick={handleDelete}
                                            className="p-1 rounded transition-colors text-red-600 hover:text-red-800"
                                            title="Delete analysis result"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                ) : !showEditAnalysis ? (
                                    <div className="ml-4">
                                        <button 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setShowOptions(true);
                                            }}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                                        >
                                            <EllipsisVertical size={12} />
                                        </button>
                                    </div>
                                ) : null}
                            </div>
                        </div>

                        {/* Details Section - Only shown when info button is pressed */}
                        {showDetails && (
                            <div className="mt-4 pt-4 border-t border-gray-300">
                                {/* Datasets Section */}
                                {(currentAnalysisResult.datasetIds.length > 0 || currentAnalysisResult.dataSourceIds?.length > 0) && (
                                    <div className="mb-3">
                                        <button
                                            onClick={() => setShowDatasets(!showDatasets)}
                                            className="flex items-center gap-2 text-xs text-gray-600 hover:text-gray-900 transition-colors"
                                        >
                                            {showDatasets ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                            <Database size={12} className="text-[#0E4F70]" />
                                            <span>Data</span>
                                        </button>
                                        {showDatasets && (
                                            <div className="mt-2 bg-gray-100 rounded border border-gray-300 p-3">
                                                <div className="space-y-2">
                                                    {currentAnalysisResult.datasetIds.map((datasetId: string, index: number) => (
                                                        <div key={datasetId} className="flex items-center gap-2 text-xs text-gray-600">
                                                            <div className="w-2 h-2 bg-[#0E4F70] rounded-full"></div>
                                                            <span>Dataset {index + 1}: {getDatasetName(datasetId)}</span>
                                                        </div>
                                                    ))}
                                                    {currentAnalysisResult.dataSourceIds?.map((dataSourceId: string, index: number) => (
                                                        <div key={dataSourceId} className="flex items-center gap-2 text-xs text-gray-600">
                                                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                                            <span>Data Source {index + 1}: {getDataSourceName(dataSourceId)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Python Code Section */}
                                {currentAnalysisResult.pythonCode && (
                                    <div className="border-t border-gray-300 pt-3">
                                        <button
                                            onClick={() => setShowCode(!showCode)}
                                            className="flex items-center gap-2 text-xs text-gray-600 hover:text-gray-900 transition-colors mb-2"
                                        >
                                            {showCode ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                            <Code size={12} className="text-green-600" />
                                            <span>Python Code</span>
                                        </button>
                                        {showCode && (
                                            <div className="overflow-x-auto">
                                                <MarkdownComponents.code
                                                    className="language-python whitespace-pre min-w-0 w-full"
                                                    children={currentAnalysisResult.pythonCode}
                                                />
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {plots && plots.map((plot: BasePlot) => (
                            <div className="mt-4 pt-4 border-t border-gray-300" key={plot.id}>
                                <div className="mb-3">
                                    <div className="h-96 bg-gray-100 rounded border border-gray-300 p-3">
                                        <EChartWrapper
                                            plot={plot}
                                            aggregationData={analysisResultData[analysisResult.id] as AggregationObjectWithRawData}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}

                        {tables && tables.map((table: BaseTable) => (
                            <div className="mt-4 pt-4 border-t border-gray-300" key={table.id}>
                                <TablesItem
                                    table={table}
                                    aggregationData={analysisResultData[analysisResult.id] as AggregationObjectWithRawData}
                                    analysisResultId={analysisResult.id}
                                    onDelete={(tableId) => deleteTable({ tableId })}
                                    onUpdate={(tableId, tableUpdate) => updateTable({ tableId, tableUpdate })}
                                />
                            </div>
                        ))}

                        <div className="flex">
                            <button
                                onClick={handlePlot}
                                disabled={isLoadingData}
                                className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                <BarChart3 size={16} />
                                <span>Create plot</span>
                            </button>
                            <button
                                onClick={handleTable}
                                disabled={isLoadingData}
                                className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                <Database size={16} />
                                <span>Create table</span>
                            </button>
                        </div>
                    </>
                )}
            </div>
            {!isDragging && analysisResult.nextType === null && analysisResult.nextId === null && (
                <DnDComponent
                    nextType={null}
                    nextId={null}
                    sectionId={analysisResult.sectionId}
                />
            )}
            <ConfirmationPopup
                isOpen={showDeleteConfirmation}
                message="Are you sure you want to delete this analysis result? This action cannot be undone."
                onConfirm={handleConfirmDelete}
                onCancel={() => setShowDeleteConfirmation(false)}
            />

            <PlotConfigurationPopup
                isOpen={showPlotConfiguration}
                onClose={() => setShowPlotConfiguration(false)}
                availableColumns={availableColumns}
                analysisResultId={analysisResult.id}
            />

            <TableConfigurationPopup
                isOpen={showTableConfiguration}
                onClose={() => setShowTableConfiguration(false)}
                availableColumns={availableColumns}
                analysisResultId={analysisResult.id}
            />
        </div>
    );
}