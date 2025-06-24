import React from 'react';
import { Handle, Position } from '@xyflow/react';

const AnalysisNode = ({ data }: { data: { label: string; id: string; onClick: () => void } }) => (
  <div 
    className="px-4 py-2 shadow-md rounded-md bg-[#1a1625]/80 border-2 border-[#271a30] cursor-pointer hover:bg-[#2a1c30]"
    onClick={data.onClick}
  >
    <div className="flex items-center">
      <div className="rounded-full w-12 h-12 flex items-center justify-center bg-[#2a1c30]">
        <svg className="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </div>
      <div className="ml-2">
        <div className="text-lg font-bold text-white">{data.label}</div>
        <div className="text-purple-300">Analysis</div>
      </div>
    </div>
    <Handle type="target" position={Position.Left} style={{ background: '#6366f1' }} />
  </div>
);

export default AnalysisNode;
