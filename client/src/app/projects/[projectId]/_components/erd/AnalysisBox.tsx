import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { BarChart3 } from 'lucide-react';
import { AnalysisJobResultMetadata } from '@/types/analysis';

interface AnalysisBoxProps {
  analysis: AnalysisJobResultMetadata;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}

export default function AnalysisBox({ analysis, onClick }: AnalysisBoxProps) {
  const isDisabled = !onClick;
  
  return (
    <div 
      className={`px-4 py-2 shadow-md rounded-md bg-[#1a1625]/80 border-2 border-[#271a30] relative ${
        isDisabled 
          ? 'cursor-default opacity-60' 
          : 'cursor-pointer hover:bg-[#2a1c30] hover:border-[#3a1c40]'
      }`}
      onClick={onClick ? onClick : undefined}
    >
      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-[#2a1c30] border border-purple-500/30">
          <BarChart3 className="w-6 h-6 text-purple-300" />
        </div>
        <div className="ml-2">
          <div className="text-lg font-mono text-white">{analysis.name}</div>
          <div className="text-purple-300 font-mono text-xs">Analysis</div>
        </div>
      </div>
      <Handle type="target" position={Position.Left} style={{ background: '#6366f1' }} />
    </div>
  );
}
