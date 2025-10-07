import React from 'react';   
import { Database } from 'lucide-react';
import { DataSource } from '@/types/data-sources';

interface DataSourceBoxProps {
  dataSource: DataSource;
  gradientClass: string | undefined;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function DataSourceBox({ dataSource, gradientClass, onClick }: DataSourceBoxProps) {
  const isDisabled = !onClick;
  
  return (
  <div
    className={`px-3 py-3 shadow-md rounded-md border-2 border-gray-600 relative min-w-[100px] max-w-[220px] ${
      isDisabled
        ? 'cursor-default opacity-60'
        : 'cursor-pointer hover:bg-[#6b7280]/10 hover:border-[#6b7280]'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex flex-col">
      <div className="flex items-center mb-2">
        <div className={`rounded-full w-6 h-6 flex items-center justify-center bg-gray-500/10 border border-gray-400/30 ${gradientClass || ''} mr-2`}>
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
