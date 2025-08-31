import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Dataset } from '@/types/data-objects';
import { Folder } from 'lucide-react';

interface DatasetProps {
  dataset: Dataset;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function DatasetBox({ dataset, onClick }: DatasetProps) {
  const isDisabled = !onClick;
  
  return (
  <div 
    className={`px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-blue-500/20 relative ${
      isDisabled 
        ? 'cursor-default opacity-60' 
        : 'cursor-pointer hover:bg-blue-500/5 hover:border-blue-500/40'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex items-center">
      <div className={`rounded-full w-12 h-12 flex items-center justify-center bg-blue-500/10 border border-blue-400/30`}>
        <Folder className="w-6 h-6 text-blue-400" />
      </div>
      <div className="ml-2">
        <div className="text-lg font-mono text-gray-200">{dataset.name}</div>
        <div className="text-blue-400 font-mono text-xs">Dataset</div>
      </div>
    </div>

    <Handle type="source" position={Position.Right} style={{ background: '#6366f1' }} />
  </div>
  );
}
