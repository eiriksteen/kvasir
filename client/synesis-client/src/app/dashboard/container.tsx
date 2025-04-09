'use client';

import { useState } from 'react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import { useRefreshDatasets, useRefreshJobs } from '@/hooks/apiHooks';
import OntologyBar from "@/components/ontologyBar";
import Chatbot from "@/components/chatbot";
import UserHeader from "@/components/userHeader";
import { Job } from '@/types/jobs';

interface DashboardProps {
  session: Session;
}

export default function DashboardContainer({ session }: DashboardProps) {

  const [datasetsInContext, setDatasetsInContext] = useState<TimeSeriesDataset[]>([]);
  const [automationsInContext, setAutomationsInContext] = useState<Automation[]>([]);
  const [addedJobs, setAddedJobs] = useState<Job[]>([]);

  useRefreshDatasets(addedJobs);
  useRefreshJobs(addedJobs);

  const handleAddDatasetToContext = (dataset: TimeSeriesDataset) => {
    if (!datasetsInContext.some(d => d.id === dataset.id)) {
      setDatasetsInContext(prev => [...prev, dataset]);
    }
  };

  const handleRemoveDatasetFromContext = (datasetId: string) => {
    setDatasetsInContext(prev => prev.filter(d => d.id !== datasetId));
  };

  const handleAddAutomationToContext = (automation: Automation) => {
    if (!automationsInContext.some(a => a.id === automation.id)) {
      setAutomationsInContext(prev => [...prev, automation]);
    }
  };

  const handleRemoveAutomationFromContext = (automationId: string) => {
    setAutomationsInContext(prev => prev.filter(a => a.id !== automationId));
  };

  return (
    <SessionProvider session={session}>
      <div className="flex flex-col h-full bg-zinc-950">
        <UserHeader 
          addedJobs={addedJobs}
          setAddedJobs={setAddedJobs}
        />
        <OntologyBar 
          datasetsInContext={datasetsInContext}
          automationsInContext={automationsInContext}
          onAddDatasetToContext={handleAddDatasetToContext}
          onRemoveDatasetFromContext={handleRemoveDatasetFromContext}
          onAddAutomationToContext={handleAddAutomationToContext}
          onRemoveAutomationFromContext={handleRemoveAutomationFromContext}
          addedJobs={addedJobs}
          setAddedJobs={setAddedJobs}
        />
        <Chatbot 
          datasetsInContext={datasetsInContext}
          automationsInContext={automationsInContext}
          onRemoveDatasetFromContext={handleRemoveDatasetFromContext}
          onRemoveAutomationFromContext={handleRemoveAutomationFromContext}
        />
      </div>
    </SessionProvider>
  );
} 