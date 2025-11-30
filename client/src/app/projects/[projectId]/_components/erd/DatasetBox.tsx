import React from 'react';
import { Folder } from 'lucide-react';
import { UUID } from 'crypto';
import { useMountedDataset } from '@/hooks/useOntology';
import { useAgentContext } from '@/hooks/useAgentContext';
import { getEntityBoxClasses } from '@/lib/entityColors';

interface DatasetProps {
  datasetId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function DatasetBox({ datasetId, projectId, openTab }: DatasetProps) {
  const dataset = useMountedDataset(datasetId, projectId);
  const { 
    datasetsInContext, 
    addDatasetToContext, 
    removeDatasetFromContext 
  } = useAgentContext(projectId);
  
  const isInContext = datasetsInContext?.includes(datasetId);

  const handleClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removeDatasetFromContext(datasetId);
      } else {
        addDatasetToContext(datasetId);
      }
    } else {
      // Regular click - open tab
      openTab(datasetId, true);
    }
  };
  
  if (!dataset) {
    return null;
  }
  
  const colors = getEntityBoxClasses('dataset');
  
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
          <Folder className={`w-3 h-3 ${colors.iconColor}`} />
        </div>
        <div className={`${colors.labelColor} font-mono text-xs`}>Dataset</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 break-words">{dataset.name}</div>
      </div>
    </div>
  </div>
  );
}
