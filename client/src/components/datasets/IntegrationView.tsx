'use client';

import { useState, useEffect, useMemo } from 'react';
import { useDatasets } from '@/hooks/useDatasets';
import IntegrationChat from './IntegrationChat';

interface IntegrationViewProps {
  datasetId: string;
}

export default function IntegrationView({ datasetId }: IntegrationViewProps) {
  const { datasets } = useDatasets();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Find the current dataset and get its integration jobs
  const currentDataset = datasets?.timeSeries?.find(dataset => dataset.id === datasetId);
  const datasetJobs = useMemo(() => currentDataset?.integrationJobs || [], [currentDataset?.integrationJobs]);

  // Auto-select the first job if available and no job is currently selected
  useEffect(() => {
    if (datasetJobs.length > 0 && !selectedJobId) {
      setSelectedJobId(datasetJobs[0].id);
    }
  }, [datasetJobs, selectedJobId]);

  const selectedJob = datasetJobs.find(job => job.id === selectedJobId);

  return (
    <div className="flex flex-col h-full bg-[#050a14] rounded-lg shadow-sm">
      {selectedJob ? (
        <IntegrationChat job={selectedJob} />
      ) : (
        <div className="flex flex-col justify-center items-center h-full text-zinc-500">
          <p>No integration job found for this dataset</p>
        </div>
      )}
    </div>
  );
} 