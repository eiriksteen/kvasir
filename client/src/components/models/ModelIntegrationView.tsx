'use client';

import { useState, useEffect, useMemo } from 'react';
import { useModels } from '@/hooks/useModels';
import ModelIntegrationChat from './ModelIntegrationChat';

interface ModelIntegrationViewProps {
  modelId: string;
}

export default function ModelIntegrationView({ modelId }: ModelIntegrationViewProps) {
  const { models } = useModels();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Find the current model and get its integration jobs  
  const currentModel = models?.find(model => model.id === modelId);
  const modelJobs = useMemo(() => currentModel?.integrationJobs || [], [currentModel?.integrationJobs]);

  // Auto-select the first job if available and no job is currently selected
  useEffect(() => {
    if (modelJobs.length > 0 && !selectedJobId) {
      setSelectedJobId(modelJobs[0].id);
    }
  }, [modelJobs, selectedJobId]);

  const selectedJob = modelJobs.find(job => job.id === selectedJobId);

  return (
    <div className="flex flex-col h-full bg-[#050a14] rounded-lg shadow-sm">
      {selectedJob ? (
        <ModelIntegrationChat job={selectedJob} />
      ) : (
        <div className="flex flex-col justify-center items-center h-full text-zinc-500">
          <p>No integration job found for this model</p>
        </div>
      )}
    </div>
  );
} 