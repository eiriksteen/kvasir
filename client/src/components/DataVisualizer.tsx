import { TimeSeriesDataset } from '@/types/datasets';
import { useAgentContext } from '@/hooks'
import { TimeSeriesVisualizerCompact, TimeSeriesVisualizerFull } from '@/components/TimeSeriesVisualizer';
import { useState } from 'react';

export default function DataVisualizer() {
  const { datasetsInContext } = useAgentContext();
  const timeSeriesDatasets = datasetsInContext?.timeSeries;
  const [selectedDataset, setSelectedDataset] = useState<TimeSeriesDataset | null>(null);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      {timeSeriesDatasets?.map((dataset: TimeSeriesDataset) => (
        selectedDataset?.id === dataset.id ? (
          <TimeSeriesVisualizerFull
            key={dataset.id}
            dataset={dataset}
            onClose={() => setSelectedDataset(null)}
          />
        ) : (
          <TimeSeriesVisualizerCompact
            key={dataset.id}
            dataset={dataset}
            onClick={() => setSelectedDataset(dataset)}
          />
        )
      ))}
    </div>
  );
}