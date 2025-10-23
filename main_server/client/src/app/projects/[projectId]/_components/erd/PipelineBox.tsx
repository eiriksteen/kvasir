import React from 'react';
import { Zap, Play, Square } from 'lucide-react';
import { PipelineRunInDB } from '@/types/pipeline';
import { usePipeline } from '@/hooks/usePipelines';
import { UUID } from 'crypto';

interface PipelineBoxProps {
  pipelineId: UUID;
  projectId: UUID;
  onClick?: () => void;
}

export default function PipelineBox({ pipelineId, projectId, onClick}: PipelineBoxProps) {
  const isDisabled = !onClick;
  const { pipeline, pipelineRuns, triggerRunPipeline } = usePipeline(pipelineId, projectId);
  const isRunning = pipelineRuns.some((run: PipelineRunInDB) => run.status === 'running');

  const handleStopClick = () => {
    console.log('Stop pipeline clicked:', pipelineId);
  };

  if (!pipeline) {
    return null;
  }

  
  return (
    <div className="flex shadow-md border-2 border-[#840B08] rounded-md min-w-[100px] max-w-[280px] overflow-hidden">
      {/* Main box content */}
      <div
        className={`px-3 py-3 flex-1 min-w-0 ${
          isDisabled
            ? 'cursor-default opacity-60'
            : 'cursor-pointer hover:bg-[#840B08]/10'
        }`}
        onClick={onClick ? onClick : undefined}
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
      
      {/* Run/Stop button */}
      <button
        onClick={isRunning ? handleStopClick : triggerRunPipeline}
        className={`w-12 px-3 py-3 border-l-2 border-[#840B08] flex-shrink-0 ${
          isDisabled
            ? 'cursor-default opacity-60'
            : 'cursor-pointer hover:bg-[#840B08]/10'
        } flex items-center justify-center transition-colors`}
        disabled={isDisabled}
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
