import React from 'react';
import { Brain } from 'lucide-react';
import { UUID } from 'crypto';
import { useMountedModelInstantiated } from '@/hooks/useOntology';
import { useAgentContext } from '@/hooks/useAgentContext';
import { getEntityBoxClasses } from '@/lib/entityColors';

interface ModelInstantiatedBoxProps {
  modelInstantiatedId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function ModelInstantiatedBox({ modelInstantiatedId, projectId, openTab }: ModelInstantiatedBoxProps) {
  const modelInstantiated = useMountedModelInstantiated(modelInstantiatedId, projectId);
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

  const colors = getEntityBoxClasses('model_instantiated');

  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer ${colors.bgHover} ${colors.borderHover} ${
      isInContext 
        ? `${colors.border} ${colors.bgInContext} ${colors.ring}` 
        : colors.border
    }`}
    onClick={handleClick}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className={`rounded-full w-6 h-6 flex items-center justify-center ${colors.iconBg} border ${colors.iconBorder} mr-2`}>
          <Brain className={`w-3 h-3 ${colors.iconColor}`} />
        </div>
        <div className={`${colors.labelColor} font-mono text-xs`}>Model</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 break-words">{modelInstantiated.name}</div>
      </div>
      </div>
    </div>
  );
}
