'use client';

import DatasetMini from './DatasetMini';
import DatasetCompact from './DatasetCompact';
import { useState } from 'react';
import DatasetFull from './DatasetFull';
import { useTimeSeriesDatasetMetadata, useTimeSeriesEntityMetadata } from '@/hooks/useTimeSeriesDataset';

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
    <>
    {currentView === 'mini' && <DatasetMini dataset={dataset} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'compact' && <DatasetCompact dataset={dataset} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'full' && <DatasetFull 
    dataset={dataset} 
    entities={entities} 
    gradientClass={gradientClass} 
    onClose={() => setCurrentView(defaultView)} 
    />}
    </>
  );
} 