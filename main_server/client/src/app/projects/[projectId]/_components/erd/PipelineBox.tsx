import React from 'react';
import { Zap, Play, Square } from 'lucide-react';
import { PipelineRunInDB } from '@/types/pipeline';
import { usePipeline } from '@/hooks/usePipelines';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';

interface PipelineBoxProps {
  pipelineId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null, closable?: boolean) => void;
}

export default function PipelineBox({ pipelineId, projectId, openTab }: PipelineBoxProps) {
  const { pipeline, pipelineRuns, triggerRunPipeline } = usePipeline(pipelineId, projectId);
  const { 
    pipelinesInContext, 
    addPipelineToContext, 
    removePipelineFromContext 
  } = useAgentContext(projectId);
  const isRunning = pipelineRuns.some((run: PipelineRunInDB) => run.status === 'running');
  
  const isInContext = pipelinesInContext.includes(pipelineId);

  const handleStopClick = () => {
    console.log('Stop pipeline clicked:', pipelineId);
  };

  const handleMainBoxClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removePipelineFromContext(pipelineId);
      } else {
        addPipelineToContext(pipelineId);
      }
    } else {
      // Regular click - open tab
      openTab(pipelineId, true);
    }
  };

  if (!pipeline) {
    return null;
  }

  
  return (
    <div className={`flex shadow-md border-2 rounded-md min-w-[100px] max-w-[280px] overflow-hidden ${
      isInContext 
        ? 'border-[#840B08] bg-[#840B08]/10 ring-2 ring-[#840B08]/30' 
        : 'border-[#840B08]'
    }`}>

      <div
        className="px-3 py-3 flex-1 min-w-0 cursor-pointer hover:bg-[#840B08]/10"
        onClick={handleMainBoxClick}
      >
        <div className="flex flex-col">
          <div className="flex items-center mb-2">
            <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#840B08]/10 border border-[#840B08]/30 mr-2">
              <Zap className="w-3 h-3 text-[#840B08]" />
            </div>
            <div className="text-[#840B08] font-mono text-xs">Pipeline</div>
          </div>
          <div>
            <div className="text-xs font-mono text-gray-800 truncate">{pipeline.name}</div>
          </div>
        </div>
      </div>
      
      <button
        onClick={isRunning ? handleStopClick : triggerRunPipeline}
        className="w-12 px-3 py-3 border-l-2 border-[#840B08] flex-shrink-0 cursor-pointer hover:bg-[#840B08]/10 flex items-center justify-center transition-colors"
      >
        {isRunning ? (
          <div className="relative w-6 h-6 flex items-center justify-center">
            {/* Loading spinner circle */}
            <div className="w-6 h-6 rounded-full border-2 border-[#840B08]/20 border-t-[#840B08] animate-spin" />
            {/* Stop square in the center */}
            <Square className="absolute w-2 h-2 text-[#840B08] fill-[#840B08]" />
          </div>
        ) : (
          <Play className="w-4 h-4 text-[#840B08] fill-[#840B08]" />
        )}
      </button>
    </div>
  );
}
