import React from 'react';
import { BarChart3 } from 'lucide-react';
import { UUID } from 'crypto';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useAgentContext } from '@/hooks/useAgentContext';

interface AnalysisBoxProps {
  analysisId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function AnalysisBox({ analysisId, projectId, openTab }: AnalysisBoxProps) {
  const { currentAnalysisObject } = useAnalysis(projectId, analysisId);
  const { 
    analysesInContext, 
    addAnalysisToContext, 
    removeAnalysisFromContext 
  } = useAgentContext(projectId);
  
  const isInContext = analysesInContext.includes(analysisId);

  const handleClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removeAnalysisFromContext(analysisId);
      } else {
        addAnalysisToContext(analysisId);
      }
    } else {
      // Regular click - open tab
      openTab(analysisId, true);
    }
  };
  
  if (!currentAnalysisObject) {
    return null;
  }
  
  return (
    <div
      className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer hover:bg-[#004806]/10 hover:border-[#004806] ${
        isInContext 
          ? 'border-[#004806] bg-[#004806]/10 ring-2 ring-[#004806]/30' 
          : 'border-[#004806]'
      }`}
      onClick={handleClick}
    >
      <div className="flex flex-col">
        <div className="flex items-center mb-2">
          <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#004806]/10 border border-[#004806]/30 mr-2">
            <BarChart3 className="w-3 h-3 text-[#004806]" />
          </div>
          <div className="text-[#004806] font-mono text-xs">Analysis</div>
        </div>
        <div>
          <div className="text-xs font-mono text-gray-800 break-words">{currentAnalysisObject.name}</div>
        </div>
      </div>
    </div>
  );
}
