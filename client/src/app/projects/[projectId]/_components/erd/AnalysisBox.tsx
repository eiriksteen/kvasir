import React from 'react';
import { BarChart3 } from 'lucide-react';
import { UUID } from 'crypto';
import { useAgentContext } from '@/hooks/useAgentContext';
import { useMountedAnalysis } from '@/hooks/useOntology';
import { getEntityBoxClasses } from '@/lib/entityColors';

interface AnalysisBoxProps {
  analysisId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function AnalysisBox({ analysisId, projectId, openTab }: AnalysisBoxProps) {
  const analysis = useMountedAnalysis(analysisId, projectId);
  const { 
    analysesInContext, 
    addAnalysisToContext,
    removeAnalysisFromContext
  } = useAgentContext(projectId);
  
  const isInContext = analysesInContext?.includes(analysisId);

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
  
  if (!analysis) {
    return null;
  }
  
  const colors = getEntityBoxClasses('analysis');
  
  return (
    <div
      className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer ${colors.bgHover} ${colors.borderHover} ${
        isInContext 
          ? `${colors.border} ${colors.bgInContext} ${colors.ring}` 
          : colors.border
      }`}
      onClick={handleClick}
    >
      <div className="flex flex-col">
        <div className="flex items-center mb-2">
          <div className={`rounded-full w-6 h-6 flex items-center justify-center ${colors.iconBg} border ${colors.iconBorder} mr-2`}>
            <BarChart3 className={`w-3 h-3 ${colors.iconColor}`} />
          </div>
          <div className={`${colors.labelColor} font-mono text-xs`}>Analysis</div>
        </div>
        <div>
          <div className="text-xs font-mono text-gray-800 break-words">{analysis.name}</div>
        </div>
      </div>
    </div>
  );
}
