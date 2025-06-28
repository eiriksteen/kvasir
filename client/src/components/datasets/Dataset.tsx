'use client';

import DatasetMini from './DatasetMini';
import DatasetCompact from './DatasetCompact';
import { useState } from 'react';
import DatasetFull from './DatasetFull';
import { useTimeSeriesDatasetMetadata, useTimeSeriesEntityMetadata } from '@/hooks/useTimeSeriesDataset';
import { Handle, Position } from '@xyflow/react';
import { createPortal } from 'react-dom';

interface DatasetProps {
  datasetId: string;
  gradientClass: string;
  defaultView: 'mini' | 'compact' | 'full';
}

export default function Dataset({ datasetId, gradientClass, defaultView }: DatasetProps) {

  const [currentView, setCurrentView] = useState<DatasetProps['defaultView']>(defaultView);
  const { dataset } = useTimeSeriesDatasetMetadata(datasetId);
  const { entities } = useTimeSeriesEntityMetadata(datasetId);

  if (!dataset) return null;

  return (
    <div>
    {currentView === 'mini' && <DatasetMini dataset={dataset} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'compact' && <DatasetCompact dataset={dataset} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'full' && createPortal(
      <DatasetFull 
        dataset={dataset} 
        entities={entities} 
        gradientClass={gradientClass} 
        onClose={() => setCurrentView(defaultView)} 
      />,
      document.body
    )}
    <Handle type="source" position={Position.Right} style={{ background: '#6366f1' }} />
    </div>
  );
} 