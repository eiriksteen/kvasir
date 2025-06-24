import { TimeSeriesDataset } from '@/types/datasets';
import { useAgentContext } from '@/hooks'
import { TimeSeriesVisualizer } from '@/components/data-visualization/TimeSeriesVisualizer';
import { useState } from 'react';

export default function DataVisualizer() {
  const { datasetsInContext } = useAgentContext();
  const timeSeriesDatasets = datasetsInContext?.timeSeries;
  const [selectedDataset, setSelectedDataset] = useState<TimeSeriesDataset | null>(null);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      {timeSeriesDatasets?.map((dataset: TimeSeriesDataset) => (
        <TimeSeriesVisualizer
          key={dataset.id}
          datasetId={dataset.id}
          mode={selectedDataset?.id === dataset.id ? 'full' : 'compact'}
          onClick={() => setSelectedDataset(dataset)}
          onClose={() => setSelectedDataset(null)}
        />
      ))}
    </div>
  );
}