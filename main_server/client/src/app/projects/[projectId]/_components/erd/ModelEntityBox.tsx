import React from 'react';
import { Brain } from 'lucide-react';
import { UUID } from 'crypto';
import { useModelEntity } from '@/hooks/useModelEntities';

interface ModelEntityBoxProps {
  modelEntityId: UUID;
  projectId: UUID;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function ModelEntityBox({ modelEntityId, projectId, onClick }: ModelEntityBoxProps) {
  const { modelEntity } = useModelEntity(projectId, modelEntityId);
  const isDisabled = !onClick;

  if (!modelEntity) {
    return null;
  }

  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 border-[#491A32] relative min-w-[100px] max-w-[220px] ${
      isDisabled
        ? 'cursor-default opacity-60'
        : 'cursor-pointer hover:bg-[#491A32]/10 hover:border-[#491A32]'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#491A32]/10 border border-[#491A32]/30 mr-2">
          <Brain className="w-3 h-3 text-[#491A32]" />
        </div>
        <div className="text-[#491A32] font-mono text-xs">Model</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 truncate">{modelEntity.name}</div>
      </div>
      </div>
    </div>
  );
}
