import React from 'react';
import { Brain } from 'lucide-react';
import { UUID } from 'crypto';
import { useModelEntity } from '@/hooks/useModelEntities';
import { useAgentContext } from '@/hooks/useAgentContext';

interface ModelEntityBoxProps {
  modelInstantiatedId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function ModelEntityBox({ modelInstantiatedId, projectId, openTab }: ModelEntityBoxProps) {
  const { modelInstantiated } = useModelEntity(projectId, modelInstantiatedId);
  const { 
    modelsInstantiatedInContext, 
    addModelEntityToContext, 
    removeModelEntityFromContext 
  } = useAgentContext(projectId);
  
  const isInContext = modelsInstantiatedInContext.includes(modelInstantiatedId);

  const handleClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removeModelEntityFromContext(modelInstantiatedId);
      } else {
        addModelEntityToContext(modelInstantiatedId);
      }
    } else {
      // Regular click - open tab
      openTab(modelInstantiatedId, true);
    }
  };

  if (!modelInstantiated) {
    return null;
  }

  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer hover:bg-[#491A32]/10 hover:border-[#491A32] ${
      isInContext 
        ? 'border-[#491A32] bg-[#491A32]/10 ring-2 ring-[#491A32]/30' 
        : 'border-[#491A32]'
    }`}
    onClick={handleClick}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#491A32]/10 border border-[#491A32]/30 mr-2">
          <Brain className="w-3 h-3 text-[#491A32]" />
        </div>
        <div className="text-[#491A32] font-mono text-xs">Model</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 break-words">{modelInstantiated.name}</div>
      </div>
      </div>
    </div>
  );
}
