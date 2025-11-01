import React from 'react';   
import { Database } from 'lucide-react';
import { UUID } from 'crypto';
import { useDataSource } from '@/hooks/useDataSources';
import { useAgentContext } from '@/hooks/useAgentContext';

interface DataSourceBoxProps {
  dataSourceId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null, closable?: boolean) => void;
}

export default function DataSourceBox({ dataSourceId, projectId, openTab }: DataSourceBoxProps) {
  const { dataSource } = useDataSource(projectId, dataSourceId);
  const { 
    dataSourcesInContext, 
    addDataSourceToContext, 
    removeDataSourceFromContext 
  } = useAgentContext(projectId);
  
  const isInContext = dataSourcesInContext.includes(dataSourceId);

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
  
  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 relative min-w-[100px] max-w-[220px] cursor-pointer hover:bg-[#6b7280]/10 hover:border-[#6b7280] ${
      isInContext 
        ? 'border-[#6b7280] bg-[#6b7280]/20 ring-4 ring-[#6b7280]/50 shadow-lg' 
        : 'border-gray-600'
    }`}
    onClick={handleClick}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className="rounded-full w-6 h-6 flex items-center justify-center bg-gray-500/10 border border-gray-400/30 mr-2">
          <Database className="w-3 h-3 text-gray-400" />
        </div>
        <div className="text-gray-600 font-mono text-xs">Data Source</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 truncate">{dataSource.type==="file" ? dataSource.typeFields?.fileName : dataSource.name}</div>
      </div>
    </div>

  </div>
  );
}
