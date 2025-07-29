import React from 'react';
import { Handle, Position } from '@xyflow/react';   
import { Database } from 'lucide-react';
import { DataSource } from '@/types/data-integration';

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
    className={`px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-emerald-500/20 relative ${
      isDisabled 
        ? 'cursor-default opacity-60' 
        : 'cursor-pointer hover:bg-emerald-500/5 hover:border-emerald-500/40'
    }`}
    onClick={onClick ? onClick : undefined}
  >
    <div className="flex items-center">
      <div className={`rounded-full w-12 h-12 flex items-center justify-center bg-emerald-500/10 border border-emerald-500/30 ${gradientClass || ''}`}>
        <Database className="w-6 h-6 text-emerald-400" />
      </div>
      <div className="ml-2">
        <div className="text-lg font-mono text-gray-200">{dataSource.name}</div>
        <div className="text-emerald-400 font-mono text-xs">Data Source</div>
      </div>
    </div>

    <Handle type="source" position={Position.Right} style={{ background: '#10b981' }} />
  </div>
  );
}
