import React from 'react';
import { Folder } from 'lucide-react';
import { UUID } from 'crypto';
import { useMountedDataset } from '@/hooks/useOntology';
import { useAgentContext } from '@/hooks/useAgentContext';

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
  
  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer hover:bg-[#0E4F70]/10 hover:border-[#0E4F70] ${
      isInContext 
        ? 'border-[#0E4F70] bg-[#0E4F70]/10 ring-2 ring-[#0E4F70]/30' 
        : 'border-[#0E4F70]'
    }`}
    onClick={handleClick}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className={`rounded-full w-6 h-6 flex items-center justify-center bg-[#0E4F70]/10 border border-[#0E4F70]/30 mr-2`}>
          <Folder className="w-3 h-3 text-[#0E4F70]" />
        </div>
        <div className="text-[#0E4F70] font-mono text-xs">Dataset</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 break-words">{dataset.name}</div>
      </div>
    </div>
  </div>
  );
}
