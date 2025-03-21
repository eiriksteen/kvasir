'use client';

import { useState } from 'react';
import OntologyBar from '@/components/ontologyBar';
import Chatbot from '@/components/chatbot';
import { TimeSeriesDataset, Automation } from '@/types/datasets';
import AddDataset from '@/components/addDataset';
import UserHeader from '@/components/userHeader';
import { JobMetadata } from '@/types/jobs';

// Empty automations array since they're not implemented yet
const EMPTY_AUTOMATIONS: Automation[] = [];

interface DashboardProps {
  datasets: TimeSeriesDataset[];
  integrationJobs: JobMetadata[];
  analysisJobs: JobMetadata[];
  automationJobs: JobMetadata[];
}

export default function DashboardContainer({ datasets, integrationJobs, analysisJobs, automationJobs }: DashboardProps) {
  const [automations] = useState<Automation[]>(EMPTY_AUTOMATIONS);
  const [datasetsInContext, setDatasetsInContext] = useState<TimeSeriesDataset[]>([]);
  const [showAddDataset, setShowAddDataset] = useState(false);

  const handleAddDatasetToContext = (dataset: TimeSeriesDataset) => {
    if (!datasetsInContext.some(d => d.id === dataset.id)) {
      setDatasetsInContext(prev => [...prev, dataset]);
    }
  };

  const handleRemoveDatasetFromContext = (datasetId: string) => {
    setDatasetsInContext(prev => prev.filter(d => d.id !== datasetId));
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      <UserHeader 
        integrationJobs={integrationJobs}
        analysisJobs={analysisJobs}
        automationJobs={automationJobs}
      />
      <OntologyBar 
        datasets={datasets}
        automations={automations}
        datasetsInContext={datasetsInContext} 
        onAddDatasetToContext={handleAddDatasetToContext}
        onRemoveDatasetFromContext={handleRemoveDatasetFromContext} 
        onOpenAddDataset={() => setShowAddDataset(true)}
      />
      <Chatbot 
        selectedDatasets={datasetsInContext} 
        onRemoveDataset={handleRemoveDatasetFromContext}
      />
      <AddDataset 
        isOpen={showAddDataset}
        onClose={() => setShowAddDataset(false)}
        onAdd={() => {
          // Refresh the datasets after adding a new one
          setDatasetsInContext(prev => [...prev]);
        }}
      />
    </div>
  );
} 