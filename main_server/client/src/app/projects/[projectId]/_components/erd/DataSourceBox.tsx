import React from 'react';   
import { Database } from 'lucide-react';
import { UUID } from 'crypto';
import { useDataSource } from '@/hooks/useDataSources';

interface DataSourceBoxProps {
  dataSourceId: UUID;
}

export default function DataSourceBox({ dataSourceId }: DataSourceBoxProps) {
  const { dataSource } = useDataSource(dataSourceId);
  
  if (!dataSource) {
    return null;
  }
  
  return (
  <div
    className="px-3 py-3 shadow-md rounded-md border-2 border-gray-600 relative min-w-[100px] max-w-[220px] cursor-pointer hover:bg-[#6b7280]/10 hover:border-[#6b7280]"
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className="rounded-full w-6 h-6 flex items-center justify-center bg-gray-500/10 border border-gray-400/30 mr-2">
          <Database className="w-3 h-3 text-gray-400" />
        </div>
        <div className="text-gray-600 font-mono text-xs">Data Source</div>
      </div>
      <div>
        <div className="text-xs font-mono text-gray-800 truncate">{dataSource.name}</div>
      </div>
    </div>

  </div>
  );
}
