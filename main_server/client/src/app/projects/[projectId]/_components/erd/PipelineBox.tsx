import React from 'react';
import { Zap } from 'lucide-react';
import { Pipeline } from '@/types/pipeline';

interface PipelineBoxProps {
  pipeline: Pipeline;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function PipelineBox({ pipeline, onClick }: PipelineBoxProps) {
  const isDisabled = !onClick;
  
  return (
    <div
    className={`px-3 py-3 shadow-md rounded-md border-2 border-[#840B08] relative min-w-[120px] max-w-[180px] ${
      isDisabled
        ? 'cursor-default opacity-60'
        : 'cursor-pointer hover:bg-[#840B08]/10 hover:border-[#840B08]'
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
  );
}
