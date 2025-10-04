'use client';

import { AnalysisObjectSmall } from '@/types/analysis';
import AnalysisItemStructuredTab from '@/components/info-modals/analysis/AnalysisItemStructuredTab';

interface AnalysisItemProps {
    analysis: AnalysisObjectSmall;
    onClose?: () => void;
}

export default function AnalysisItem({ analysis, onClose }: AnalysisItemProps) {

    return (
        <>
            <div className="w-full h-full bg-gray-950 overflow-hidden">
                <div className={`cursor-pointer bg-[#1a1625] h-full px-0 pb-2 relative`}>
                    <div className="flex flex-col h-full">
                        {/* Metadata Section - Compact design */}
                        {/* <div className="flex justify-between items-center px-2 py-2 relative">
                            <div className="flex-1 min-w-0">
                                <div className="text-base font-medium text-purple-300 truncate">{analysis.name}</div>
                                {showDetails && (
                                    <div className="mt-1 space-y-1">
                                        <div className="text-xs text-zinc-500">
                                            {new Date(analysis.createdAt).toLocaleDateString()}
                                        </div>
                                        {analysis.description && (
                                            <div className="text-xs text-zinc-400 truncate">{analysis.description}</div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div> */}
                        
                        {/* Content Section */}
                        <div className="flex-1 min-h-0">
                            <div className="h-full">
                                <AnalysisItemStructuredTab
                                    analysisObjectId={analysis.id}
                                    projectId={analysis.projectId}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}