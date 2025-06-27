import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Loader2, Pause, Check, X } from 'lucide-react';
import { useDatasetIsBeingCreated } from '@/hooks/useDatasets';

interface DatasetMiniProps {
  dataset: TimeSeriesDataset;
  gradientClass: string | undefined;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function DatasetMini({ dataset, gradientClass, onClick }: DatasetMiniProps) {
  const {isBeingCreated, creationJobState} = useDatasetIsBeingCreated(dataset);
  const isDisabled = !onClick;
  
  return (
  <div 
    className={`px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-[#101827] relative ${
      isDisabled 
        ? 'cursor-default opacity-60' 
        : 'cursor-pointer hover:bg-[#0a101c]'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex items-center">
      <div className={`rounded-full w-12 h-12 flex items-center justify-center bg-[#0e1a30] ${gradientClass || ''}`}>
        <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      </div>
      <div className="ml-2">
        <div className="text-sm font-mono text-gray-200">{dataset.name}</div>
        <div className="text-blue-300 font-mono text-xs">Dataset</div>
      </div>
    </div>
    {isBeingCreated && (
      <div className="absolute top-2 right-2">
        {creationJobState === 'running' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
        {creationJobState === 'paused' && <Pause className="w-4 h-4 text-blue-400" />}
        {creationJobState === 'awaiting_approval' && <Check className="w-4 h-4 text-blue-400" />}
        {creationJobState === 'failed' && <X className="w-4 h-4 text-red-400" />}
      </div>
    )}
    <Handle type="source" position={Position.Right} style={{ background: '#6366f1' }} />
  </div>
  );
}
