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
      className={`px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-orange-500/20 relative ${
        isDisabled 
          ? 'cursor-default opacity-60' 
          : 'cursor-pointer hover:bg-orange-500/5 hover:border-orange-500/40'
      }`}
      onClick={onClick ? onClick : undefined}
    >
      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-orange-500/10 border border-orange-500/30">
          <Zap className="w-6 h-6 text-orange-400" />
        </div>
        <div className="ml-2">
          <div className="text-lg font-mono text-gray-200">{pipeline.name}</div>
          <div className="text-orange-400 font-mono text-xs">Pipeline</div>
        </div>

      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#f97316' }} />
    </div>
  );
}
