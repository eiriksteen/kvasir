'use client';

import { useState, useRef, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { AnalysisCell, CodeCell, MarkdownCellBase } from '@/types/ontology/analysis';
import { MarkdownComponents } from '@/components/MarkdownComponents';
import { useAnalysis } from '@/hooks/useAnalysis';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { UUID } from 'crypto';
import { ChevronDown, ChevronRight, Trash2, EllipsisVertical, Move, Pencil, Save, Loader2, X } from 'lucide-react';
import DnDComponent from './DnDComponent';
import { createSmoothTextStream } from '@/lib/utils';
import EChartWrapper from '@/components/charts/EChartWrapper';
import TableWrapper from '@/components/tables/TableWrapper';
import ImageWrapper from '@/components/images/ImageWrapper';

interface CellItemProps {
    projectId: UUID;
    cell: AnalysisCell;
    analysisObjectId: UUID;
}

export default function CellItem({ projectId, cell, analysisObjectId }: CellItemProps) {
    const [showCode, setShowCode] = useState(false);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
    const [showEdit, setShowEdit] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [showOptions, setShowOptions] = useState(false);
    const optionsRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    
    const { mutateAnalysis } = useAnalysis(analysisObjectId);
    
    // Determine cell type
    const isCodeCell = cell.type === 'code';
    const codeCell = isCodeCell ? (cell.typeFields as CodeCell) : null;
    const markdownCell = !isCodeCell ? (cell.typeFields as MarkdownCellBase) : null;
    
    // Get content based on cell type
    const content = isCodeCell ? (codeCell?.output?.output || '') : (markdownCell?.markdown || '');
    const code = isCodeCell ? codeCell?.code || '' : '';
    const [editContent, setEditContent] = useState(content);
    
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
        if (showEdit && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [showEdit]);

    // Smooth streaming for content updates
    const [smoothStreamedText, setSmoothStreamedText] = useState(content);
    const streamCancelRef = useRef<{ cancel: () => void } | null>(null);
    const previousContentRef = useRef<string>(content);

    useEffect(() => {
        const previousContent = previousContentRef.current;
        
        if (content.startsWith(previousContent) && content.length > previousContent.length) {
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }

            const newText = content.slice(previousContent.length);
            
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
        } else if (content !== previousContent) {
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }

            streamCancelRef.current = createSmoothTextStream(
                content,
                setSmoothStreamedText,
                {
                    mode: 'word',
                    intervalMs: 15,
                }
            );
        }

        previousContentRef.current = content;

        return () => {
            if (streamCancelRef.current) {
                streamCancelRef.current.cancel();
            }
        };
    }, [content, cell.id]);

    // Drag functionality with dnd-kit
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: cell.id,
        data: {
            type: 'cell',
            cell: cell
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
        // TODO: Implement delete cell API call
        console.log('Delete cell:', cell.id);
        setShowDeleteConfirmation(false);
    };

    const handleUpdate = async () => {
        if (editContent.trim() && !isUpdating) {
            setIsUpdating(true);
            try {
                // TODO: Implement update cell API call
                await mutateAnalysis();
                setShowEdit(false);
            } catch (error) {
                console.error('Error updating cell:', error);
            } finally {
                setIsUpdating(false);
            }
        }
    };

    const handleCancelEdit = () => {
        setEditContent(content);
        setShowEdit(false);
    };

    // Get output data if code cell
    const output = codeCell?.output;
    const images = output?.images || [];
    const echarts = output?.echarts || [];
    const tables = output?.tables || [];

    return (
        <div className="w-full">
            {/* DnD Component - positioned above the cell, only when not dragging */}
            {!isDragging && (
                <DnDComponent
                    nextType={"analysis_result"}
                    nextId={cell.id}
                    sectionId={cell.sectionId}
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
                            <Move size={16} className="text-[#0E4F70] animate-pulse" />
                            <span className="text-sm text-[#0E4F70]">Moving cell...</span>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Main Content with Info and Delete Buttons */}
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="text-base text-gray-800 leading-relaxed text-justify">
                                    {showEdit ? (
                                        <div className="space-y-3">
                                            <textarea
                                                ref={textareaRef}
                                                value={editContent}
                                                onChange={(e) => setEditContent(e.target.value)}
                                                className="w-full px-3 py-2 text-xs rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70] resize-none"
                                                placeholder="Edit content..."
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
                                                    onClick={handleUpdate}
                                                    disabled={isUpdating || !editContent.trim()}
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
                                {showOptions && !showEdit ? (
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
                                                setShowEdit(true);
                                                setShowOptions(false);
                                            }}
                                            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                                            title="Edit cell"
                                        >
                                            <Pencil size={12} />
                                        </button>
                                        <button
                                            onClick={handleDelete}
                                            className="p-1 rounded transition-colors text-red-600 hover:text-red-800"
                                            title="Delete cell"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                ) : !showEdit ? (
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

                        {/* Code display for code cells */}
                        {isCodeCell && code && (
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
                                            {`\`\`\`python\n${code}\n\`\`\``}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Render charts */}
                        {echarts.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {echarts.map((chart) => (
                                    <div key={chart.id} className="w-full h-[450px]">
                                        <EChartWrapper projectId={projectId} chartId={chart.id}/>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Render tables */}
                        {tables.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {tables.map((table) => (
                                    <div key={table.id}>
                                        <TableWrapper tableId={table.id} projectId={projectId}/>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Render images */}
                        {images.length > 0 && (
                            <div className="mt-4 space-y-4">
                                {images.map((image) => (
                                    <div key={image.id}>
                                        <ImageWrapper imageId={image.id} projectId={projectId} />
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>
            {!isDragging && (
                <DnDComponent
                    nextType={null}
                    nextId={null}
                    sectionId={cell.sectionId}
                />
            )}
            <ConfirmationPopup
                isOpen={showDeleteConfirmation}
                message="Are you sure you want to delete this cell? This action cannot be undone."
                onConfirm={handleConfirmDelete}
                onCancel={() => setShowDeleteConfirmation(false)}
            />
        </div>
    );
}

