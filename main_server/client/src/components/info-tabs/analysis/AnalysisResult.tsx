'use client';

import Image from 'next/image';
import { useState, useMemo, useRef, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { ChevronDown, ChevronRight, Trash2, EllipsisVertical, Move, FileSearch, Pencil, Save, Loader2, X } from 'lucide-react';
import { AnalysisResult as AnalysisResultType, AnalysisStatusMessage } from '@/types/analysis';
import { MarkdownComponents } from '@/components/MarkdownComponents';
import { useAnalysis } from '@/hooks/useAnalysis';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { UUID } from 'crypto';


import DnDComponent from './DnDComponent';
import { createSmoothTextStream } from '@/lib/utils';
import EChartWrapper from '@/components/charts/EChartWrapper';
import TableWrapper from '@/components/tables/TableWrapper';

interface AnalysisResultProps {
    projectId: UUID;
    analysisResult: AnalysisResultType;
    analysisObjectId: UUID;
}

export default function AnalysisResult({ projectId, analysisResult, analysisObjectId }: AnalysisResultProps) {
    const [showCode, setShowCode] = useState(false);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    const [showEditAnalysis, setShowEditAnalysis] = useState(false);
    const [editAnalysis, setEditAnalysis] = useState(analysisResult.analysis);
    const [isUpdating, setIsUpdating] = useState(false);
    const { analysisStatusMessages, deleteAnalysisResult, updateAnalysisResult } = useAnalysis(projectId, analysisObjectId);
    const [showOptions, setShowOptions] = useState(false);
    const optionsRef = useRef<HTMLDivElement>(null);
    const analysisTextareaRef = useRef<HTMLTextAreaElement>(null);
    const [smoothStreamedText, setSmoothStreamedText] = useState(analysisResult.analysis);
    const streamCancelRef = useRef<{ cancel: () => void } | null>(null);
    
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
            message.analysisResult?.id === analysisResult.id
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
        if (latestStreamingMessage?.analysisResult) {
            return latestStreamingMessage.analysisResult.analysis;
        }
        return analysisResult.analysis;
    }, [latestStreamingMessage, analysisResult]);

    // Get the most up-to-date analysis result data (either from streaming or static)
    const currentAnalysisResult = useMemo(() => {
        if (latestStreamingMessage?.analysisResult) {
            return latestStreamingMessage.analysisResult;
        }
        return analysisResult;
    }, [latestStreamingMessage, analysisResult]);

    // Ref to track previous content for incremental streaming
    const previousDisplayContentRef = useRef<string>(displayContent);

    // Smooth streaming effect - triggers when displayContent changes
    useEffect(() => {
        const previousContent = previousDisplayContentRef.current;
        
        // Check if this is an incremental update (new text appended)
        if (displayContent.startsWith(previousContent) && displayContent.length > previousContent.length) {
            // Cancel any existing stream
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }

            // Extract only the NEW text that was appended
            const newText = displayContent.slice(previousContent.length);
            
            // Stream only the new text, appending to existing smoothStreamedText
            streamCancelRef.current = createSmoothTextStream(
                newText,
                (incrementalText) => {
                    setSmoothStreamedText(() => previousContent + incrementalText);
                },
                {
                    mode: 'word',
                    intervalMs: 15,
                }
            );
        } else if (displayContent !== previousContent) {
            // Content changed completely (not an append), restart from scratch
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }

            streamCancelRef.current = createSmoothTextStream(
                displayContent,
                setSmoothStreamedText,
                {
                    mode: 'word',
                    intervalMs: 15,
                }
            );
        }

        // Update the ref to track current content
        previousDisplayContentRef.current = displayContent;

        return () => {
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }
        };
    }, [displayContent, previousDisplayContentRef, analysisResult.id]);

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


    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowDeleteConfirmation(true);
    };

    const handleConfirmDelete = async () => {
        await deleteAnalysisResult({ analysisObjectId, analysisResultId: analysisResult.id });

    };

    const handleUpdateAnalysis = async () => {
        if (editAnalysis.trim() && !isUpdating) {
            setIsUpdating(true);
            try {
                await updateAnalysisResult({
                    analysisResultId: analysisResult.id,
                    analysisResult: {
                        id: analysisResult.id,
                        analysis: editAnalysis.trim(),
                        pythonCode: analysisResult.pythonCode,
                        nextType: analysisResult.nextType,
                        nextId: analysisResult.nextId,
                        sectionId: analysisResult.sectionId,
                        plotUrls: analysisResult.plotUrls,
                        imageUrls: analysisResult.imageUrls,
                        chartScriptPaths: analysisResult.chartScriptPaths,
                        tablePaths: analysisResult.tablePaths,
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
                className={`py-1 transition-opacity w-full min-w-0 ${
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
                                <div className="text-base text-gray-800 leading-relaxed text-justify">
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
                                            {smoothStreamedText}
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
                                        {/* <button
                                            onClick={() => {
                                                handlePlot();
                                                setShowOptions(false);
                                            }}
                                            disabled={isLoadingData}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            title="Create plot"
                                        >
                                            <BarChart3 size={12} />
                                        </button>
                                        <button
                                            onClick={() => {
                                                handleTable();
                                                setShowOptions(false);
                                            }}
                                            disabled={isLoadingData}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            title="Create table"
                                        >
                                            <Database size={12} />
                                        </button> */}
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

                        {currentAnalysisResult.pythonCode && (
                            <div>
                                <button
                                    onClick={() => setShowCode(!showCode)}
                                    className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 transition-colors"
                                >
                                    {showCode ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                    <span className="text-xs text-gray-500">Code</span>
                                </button>
                                {showCode && (
                                    <div className="overflow-x-auto">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={MarkdownComponents}
                                        >
                                            {`\`\`\`python\n${currentAnalysisResult.pythonCode}\n\`\`\``}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Render charts */}
                        {currentAnalysisResult.chartScriptPaths && currentAnalysisResult.chartScriptPaths.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {currentAnalysisResult.chartScriptPaths.map((chartScriptPath: string, index: number) => (
                                    <div key={index} className="h-96 bg-gray-50 rounded p-3">
                                        <EChartWrapper
                                            projectId={projectId}
                                            chartScriptPath={chartScriptPath}
                                        />
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Render tables */}
                        {currentAnalysisResult.tablePaths && currentAnalysisResult.tablePaths.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {currentAnalysisResult.tablePaths.map((tablePath: string, index: number) => (
                                    <div key={index} className="bg-gray-50 rounded p-3">
                                        <TableWrapper
                                            projectId={projectId}
                                            tablePath={tablePath}
                                        />
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Render images */}
                        {currentAnalysisResult.imageUrls && currentAnalysisResult.imageUrls.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {currentAnalysisResult.imageUrls.map((imageUrl: string, index: number) => (
                                    imageUrl && (
                                        <div key={index} className="max-w-2xl mx-auto">
                                            <Image 
                                                width={600}
                                                height={450}
                                                src={imageUrl}
                                                alt={`Analysis image ${index + 1}`}
                                                className="w-full h-auto rounded"
                                                unoptimized
                                            />
                                        </div>
                                    )
                                ))}
                            </div>
                        )}
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
        </div>
    );
}