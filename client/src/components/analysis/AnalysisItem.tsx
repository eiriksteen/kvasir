'use client';

import { useState } from 'react';
import { Check, Plus, Trash2, Calendar, Database, Bot, FileText } from 'lucide-react';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { useAnalysis } from '@/hooks';
import ConfirmationPopup from '../ConfirmationPopup';

interface AnalysisItemSmallProps {
    analysis: AnalysisJobResultMetadata;
    isSelected: boolean;
    onClick: () => void;
}

export default function AnalysisItemSmall({ analysis, isSelected, onClick }: AnalysisItemSmallProps) {
    const { deleteAnalysisJobResults } = useAnalysis();
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowDeleteConfirmation(true);
    };

    const handleConfirmDelete = async () => {
        await deleteAnalysisJobResults(analysis);
        setShowDeleteConfirmation(false);
    };

    return (
        <>
            <div 
                onClick={onClick}
                className={`rounded-lg cursor-pointer bg-[#1a2438] border-2 h-full border-[#1a2438]`}
            >
                <div className="flex flex-col h-full">
                    {/* Metadata Section - Fixed at top */}
                    <div className="flex justify-between items-start mb-6">
                        <div className="flex flex-col gap-4">
                            <div className="text-sm font-medium text-blue-300">Analysis Results</div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Calendar size={14} className="text-blue-400" />
                                    <span className="text-xs">{new Date(analysis.createdAt).toLocaleDateString()}</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Database size={14} className="text-blue-400" />
                                    <span className="text-xs">{analysis.numberOfDatasets} Datasets</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Bot size={14} className="text-blue-400" />
                                    <span className="text-xs">{analysis.numberOfAutomations} Automations</span>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <FileText size={14} className="text-blue-400" />
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
                                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                                        : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                                }`}
                                title={isSelected ? "Remove from context" : "Add to chat context"}
                            >
                                {isSelected ? <Check size={14} /> : <Plus size={14} />}
                            </button>
                        </div>
                    </div>

                    {/* Analysis Plan Section - Scrollable */}
                    <div className="flex flex-col gap-3 flex-1 min-h-0">
                        <div className="text-sm font-medium text-blue-300">Analysis Plan</div>
                        <div className="bg-[#0a101c] rounded-lg border border-[#1a2438] flex-1 min-h-0">
                            <div className="p-4 pb-8 h-full overflow-y-auto custom-scrollbar">
                                <div className="text-sm text-zinc-300 mb-3">
                                    {analysis.analysisPlan.analysisOverview}
                                </div>
                                <div className="space-y-2">
                                    {analysis.analysisPlan.analysisPlan.map((step, index) => (
                                        <div key={index} className="flex gap-3 text-sm">
                                            <div className="text-blue-400 font-medium min-w-[24px]">{index + 1}.</div>
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
