'use client';

import { useState } from 'react';
import { Check, Plus, Trash2, Calendar, Database, Bot, FileText, X } from 'lucide-react';
import { useAnalysis } from '@/hooks';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import { UUID } from 'crypto';
import { useAnalysisObject } from '@/hooks/useAnalysis';


// TODO: Update to match design of the other info modals

interface AnalysisInfoTabProps {
    projectId: UUID;
    analysisObjectId: UUID;
    isSelected: boolean;
    onClick: () => void;
    isModal?: boolean;
    onClose?: () => void;
}

export default function AnalysisInfoTab({ projectId, analysisObjectId, isSelected, onClick, isModal = false, onClose }: AnalysisInfoTabProps) {
    const { deleteAnalysisObject } = useAnalysisObject(projectId, analysisObjectId);
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowDeleteConfirmation(true);
    };

    const handleConfirmDelete = async () => {
        await deleteAnalysisObject({ analysisObjectId });
        setShowDeleteConfirmation(false);
        if (onClose) onClose();
    };

    if (isModal) {
        return (
            <>
                <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="relative flex w-full max-w-5xl h-[80vh] bg-white border border-gray-300 rounded-lg shadow-2xl overflow-hidden">
                        <div 
                            onClick={onClick}
                            className={`rounded-lg cursor-pointer bg-gray-50 border-2 h-full border-gray-300 p-4 relative`}
                        >
                            <button
                                onClick={onClose}
                                className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                                title="Close (Esc)"
                            >
                                <X size={20} />
                            </button>
                            <div className="flex flex-col h-full">
                                {/* Metadata Section - Fixed at top */}
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex flex-col gap-4">
                                        <div className="text-sm font-medium text-[#004806]">Analysis Results</div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="flex items-center gap-2 text-zinc-400">
                                                <Calendar size={14} className="text-[#004806]" />
                                                <span className="text-xs">{new Date(analysis.createdAt).toLocaleDateString()}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-zinc-400">
                                                <Database size={14} className="text-[#004806]" />
                                                <span className="text-xs">{analysis.numberOfDatasets} Datasets</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-zinc-400">
                                                <Bot size={14} className="text-[#004806]" />
                                                <span className="text-xs">{analysis.numberOfPipelines} Pipelines</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-zinc-400">
                                                <FileText size={14} className="text-[#004806]" />
                                                <span className="text-xs">PDF {analysis.pdfCreated ? "Available" : "Not Available"}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2 mr-8">
                                        <button 
                                            onClick={handleDelete}
                                            className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-red-600/40 to-red-700/40 text-red-300 border-red-500/30 shadow-red-900/20 hover:from-red-600/60 hover:to-red-700/60 hover:text-red-200"
                                            title="Delete analysis"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                        <button 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onClick();
                                            }}
                                            className={`p-1.5 rounded-full border shadow-md ${
                                                isSelected
                                                    ? 'bg-gradient-to-r from-[#004806] to-[#004806]/80 text-white border-[#004806] shadow-[#004806]/30'
                                                    : 'bg-gradient-to-r from-[#1a1625] to-[#271a30] text-[#004806] hover:text-white hover:from-[#004806]/80 hover:to-[#004806] border-[#004806]/50'
                                            }`}
                                            title={isSelected ? "Remove from context" : "Add to chat context"}
                                        >
                                            {isSelected ? <Check size={14} /> : <Plus size={14} />}
                                        </button>
                                    </div>
                                </div>

                                {/* Analysis Plan Section - Scrollable */}
                                <div className="flex flex-col gap-3 flex-1 min-h-0">
                                    <div className="text-sm font-medium text-[#004806]">Analysis Plan</div>
                                    <div className="bg-[#0a101c] rounded-lg border border-[#004806]/50 flex-1 min-h-0">
                                        <div className="p-4 pb-8 h-full overflow-y-auto custom-scrollbar">
                                            <div className="text-sm text-zinc-300 mb-3">
                                                {analysis.analysisPlan.analysisOverview}
                                            </div>
                                            <div className="space-y-2">
                                                {analysis.analysisPlan.analysisPlan.map((step, index) => (
                                                    <div key={index} className="flex gap-3 text-sm">
                                                        <div className="text-[#004806] font-medium min-w-[24px]">{index + 1}.</div>
                                                        <div className="text-zinc-400">
                                                            <div className="font-medium text-zinc-300">{step.stepName}</div>
                                                            <div className="text-xs mt-0.5">{step.stepDescription}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <ConfirmationPopup
                    isOpen={showDeleteConfirmation}
                    message={`Are you sure you want to delete this analysis? This action cannot be undone.`}
                    onConfirm={handleConfirmDelete}
                    onCancel={() => setShowDeleteConfirmation(false)}
                />
            </>
        );
    }

    return (
        <>
            <div 
                onClick={onClick}
                className={`rounded-lg cursor-pointer bg-[#1a1625] border-2 h-full border-[#004806]/50 p-4`}
            >
                <div className="flex flex-col h-full">
                    {/* Metadata Section - Fixed at top */}
                    <div className="flex justify-between items-start mb-6">
                        <div className="flex flex-col gap-4">
                            <div className="text-sm font-medium text-[#004806]">Analysis Results</div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Calendar size={14} className="text-[#004806]" />
                                    <span className="text-xs">{new Date(analysis.createdAt).toLocaleDateString()}</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Database size={14} className="text-[#004806]" />
                                    <span className="text-xs">{analysis.numberOfDatasets} Datasets</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Bot size={14} className="text-[#004806]" />
                                    <span className="text-xs">{analysis.numberOfPipelines} Pipelines</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <FileText size={14} className="text-[#004806]" />
                                    <span className="text-xs">PDF {analysis.pdfCreated ? "Available" : "Not Available"}</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-2 mr-8">
                            <button 
                                onClick={handleDelete}
                                className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-red-600/40 to-red-700/40 text-red-300 border-red-500/30 shadow-red-900/20 hover:from-red-600/60 hover:to-red-700/60 hover:text-red-200"
                                title="Delete analysis"
                            >
                                <Trash2 size={14} />
                            </button>
                            <button 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onClick();
                                }}
                                className={`p-1.5 rounded-full border shadow-md ${
                                    isSelected
                                        ? 'bg-gradient-to-r from-[#004806] to-[#004806]/80 text-white border-[#004806] shadow-[#004806]/30'
                                        : 'bg-gradient-to-r from-[#1a1625] to-[#271a30] text-[#004806] hover:text-white hover:from-[#004806]/80 hover:to-[#004806] border-[#004806]/50'
                                }`}
                                title={isSelected ? "Remove from context" : "Add to chat context"}
                            >
                                {isSelected ? <Check size={14} /> : <Plus size={14} />}
                            </button>
                        </div>
                    </div>

                    {/* Analysis Plan Section - Scrollable */}
                    <div className="flex flex-col gap-3 flex-1 min-h-0">
                        <div className="text-sm font-medium text-[#004806]">Analysis Plan</div>
                        <div className="bg-[#0a101c] rounded-lg border border-[#004806]/50 flex-1 min-h-0">
                            <div className="p-4 pb-8 h-full overflow-y-auto custom-scrollbar">
                                <div className="text-sm text-zinc-300 mb-3">
                                    {analysis.analysisPlan.analysisOverview}
                                </div>
                                <div className="space-y-2">
                                    {analysis.analysisPlan.analysisPlan.map((step, index) => (
                                        <div key={index} className="flex gap-3 text-sm">
                                            <div className="text-[#004806] font-medium min-w-[24px]">{index + 1}.</div>
                                            <div className="text-zinc-400">
                                                <div className="font-medium text-zinc-300">{step.stepName}</div>
                                                <div className="text-xs mt-0.5">{step.stepDescription}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <ConfirmationPopup
                isOpen={showDeleteConfirmation}
                message={`Are you sure you want to delete this analysis? This action cannot be undone.`}
                onConfirm={handleConfirmDelete}
                onCancel={() => setShowDeleteConfirmation(false)}
            />
        </>
    );
}
