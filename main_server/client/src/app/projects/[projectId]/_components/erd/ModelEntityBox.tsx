import React from 'react';
import { Brain } from 'lucide-react';
import { ModelEntity } from '@/types/model';

interface ModelEntityBoxProps {
  modelEntity: ModelEntity;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function ModelEntityBox({ modelEntity, onClick }: ModelEntityBoxProps) {
  const isDisabled = !onClick;

  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 border-emerald-600 relative min-w-[120px] max-w-[180px] ${
      isDisabled
        ? 'cursor-default opacity-60'
        : 'cursor-pointer hover:bg-emerald-50 hover:border-emerald-600'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className="rounded-full w-6 h-6 flex items-center justify-center bg-emerald-500/10 border border-emerald-500/30 mr-2">
          <Brain className="w-3 h-3 text-emerald-400" />
        </div>
        <div className="text-emerald-600 font-mono text-xs">Model</div>
      </div>
      <div>
        <div className="text-sm font-mono text-gray-800 truncate">{modelEntity.name}</div>
      </div>
      </div>
    </div>
  );
}
