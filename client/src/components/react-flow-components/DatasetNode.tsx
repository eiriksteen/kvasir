import React from 'react';
import { Handle, Position } from '@xyflow/react';

const DatasetNode = ({ data }: { data: { label: string; id: string; onClick: () => void } }) => (
  <div 
    className="px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-[#101827] cursor-pointer hover:bg-[#0a101c]"
    onClick={data.onClick}
  >
    <div className="flex items-center">
      <div className="rounded-full w-12 h-12 flex items-center justify-center bg-[#0e1a30]">
        <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      </div>
      <div className="ml-2">
        <div className="text-lg font-bold text-white">{data.label}</div>
        <div className="text-blue-300">Dataset</div>
      </div>
    </div>
    <Handle type="source" position={Position.Right} style={{ background: '#6366f1' }} />
  </div>
);

export default DatasetNode;
