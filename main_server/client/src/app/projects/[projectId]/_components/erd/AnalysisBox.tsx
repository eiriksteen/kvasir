import React from 'react';
import { BarChart3 } from 'lucide-react';
import { UUID } from 'crypto';
import { useAnalysis } from '@/hooks/useAnalysis';

interface AnalysisBoxProps {
  analysisId: UUID;
  projectId: UUID;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function AnalysisBox({ analysisId, projectId, onClick }: AnalysisBoxProps) {
  const { currentAnalysisObject } = useAnalysis(projectId, analysisId);
  const isDisabled = !onClick;
  
  if (!currentAnalysisObject) {
    return null;
  }
  
  return (
    <div
      className={`px-3 py-3 shadow-md rounded-md border-2 border-[#004806] relative min-w-[100px] max-w-[220px] ${
        isDisabled
          ? 'cursor-default opacity-60'
          : 'cursor-pointer hover:bg-[#004806]/10 hover:border-[#004806]'
      }`}
      onClick={onClick ? onClick : undefined}
    >
      <div className="flex flex-col">
        <div className="flex items-center mb-2">
          <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#004806]/10 border border-[#004806]/30 mr-2">
            <BarChart3 className="w-3 h-3 text-[#004806]" />
          </div>
          <div className="text-[#004806] font-mono text-xs">Analysis</div>
        </div>
        <div>
          <div className="text-xs font-mono text-gray-800 truncate">{currentAnalysisObject.name}</div>
        </div>
      </div>
    </div>
  );
}
