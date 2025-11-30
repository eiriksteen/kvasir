import React from 'react';   
import { Database } from 'lucide-react';
import { UUID } from 'crypto';
import { useMountedDataSource } from '@/hooks/useOntology';
import { useAgentContext } from '@/hooks/useAgentContext';
import { getEntityBoxClasses } from '@/lib/entityColors';

interface DataSourceBoxProps {
  dataSourceId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function DataSourceBox({ dataSourceId, projectId, openTab }: DataSourceBoxProps) {
  const dataSource = useMountedDataSource(dataSourceId, projectId);

  const { 
    dataSourcesInContext, 
    addDataSourceToContext, 
    removeDataSourceFromContext 
  } = useAgentContext(projectId);
  
  const isInContext = dataSourcesInContext?.includes(dataSourceId); 

  const handleClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removeDataSourceFromContext(dataSourceId);
      } else {
        addDataSourceToContext(dataSourceId);
      }
    } else {
      // Regular click - open tab
      openTab(dataSourceId, true);
    }
  };
  
  if (!dataSource) {
    return null;
  }
  
  const colors = getEntityBoxClasses('data_source');
  
  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[240px] cursor-pointer ${colors.bgHover} ${colors.borderHover} ${
      isInContext 
        ? `${colors.border} ${colors.bgInContext} ${colors.ring} shadow-lg` 
        : colors.border
    }`}
    onClick={handleClick}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className={`rounded-full w-6 h-6 flex items-center justify-center ${colors.iconBg} border ${colors.iconBorder} mr-2`}>
          <Database className={`w-3 h-3 ${colors.iconColor}`} />
        </div>
        <div className={`${colors.labelColor} font-mono text-xs`}>Data Source</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 break-words">{dataSource.name}</div>
      </div>
    </div>

  </div>
  );
}
