import React from 'react';
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
    className={`px-3 py-3 shadow-md rounded-md border-2 border-[#0E4F70] relative min-w-[120px] max-w-[180px] ${
      isDisabled
        ? 'cursor-default opacity-60'
        : 'cursor-pointer hover:bg-[#0E4F70]/10 hover:border-[#0E4F70]'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className={`rounded-full w-6 h-6 flex items-center justify-center bg-[#0E4F70]/10 border border-[#0E4F70]/30 mr-2`}>
          <Folder className="w-3 h-3 text-[#0E4F70]" />
        </div>
        <div className="text-[#0E4F70] font-mono text-xs">Dataset</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 truncate">{dataset.name}</div>
      </div>
    </div>
  </div>
  );
}
