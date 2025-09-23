import React from 'react';
import { Handle, Position } from '@xyflow/react';
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
      className={`px-3 py-3 shadow-md rounded-md bg-[#050a14] border-2 border-orange-500/20 relative min-w-[120px] max-w-[180px] ${
        isDisabled
          ? 'cursor-default opacity-60'
          : 'cursor-pointer hover:bg-orange-500/5 hover:border-orange-500/40'
      }`}
      onClick={onClick ? onClick : undefined}
    >
      <div className="flex flex-col">
        <div className="flex items-center mb-2">
          <div className="rounded-full w-6 h-6 flex items-center justify-center bg-orange-500/10 border border-orange-500/30 mr-2">
            <Zap className="w-3 h-3 text-orange-400" />
          </div>
          <div className="text-orange-400 font-mono text-xs">Pipeline</div>
        </div>
        <div>
          <div className="text-sm font-mono text-gray-200 truncate">{pipeline.name}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#f97316' }} />
    </div>
  );
}
