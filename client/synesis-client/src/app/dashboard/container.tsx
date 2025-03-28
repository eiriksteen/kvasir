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

interface DashboardProps {
  session: Session;
}

export default function DashboardContainer({ session }: DashboardProps) {

  const [datasetsInContext, setDatasetsInContext] = useState<TimeSeriesDataset[]>([]);
  const [automationsInContext, setAutomationsInContext] = useState<Automation[]>([]);
  const [integrationJobState, setIntegrationJobState] = useState<string>("");
  const [analysisJobState, setAnalysisJobState] = useState<string>("");
  const [automationJobState, setAutomationJobState] = useState<string>("");

  console.log("INTEGRATION JOB STATE", integrationJobState);
  console.log("ANALYSIS JOB STATE", analysisJobState);
  console.log("AUTOMATION JOB STATE", automationJobState);

  useRefreshDatasets(integrationJobState);
  useRefreshJobs(integrationJobState);

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
          integrationJobState={integrationJobState}
          setIntegrationJobState={setIntegrationJobState}
          analysisJobState={analysisJobState}
          setAnalysisJobState={setAnalysisJobState}
          automationJobState={automationJobState}
          setAutomationJobState={setAutomationJobState}
        />
        <OntologyBar 
          datasetsInContext={datasetsInContext}
          automationsInContext={automationsInContext}
          onAddDatasetToContext={handleAddDatasetToContext}
          onRemoveDatasetFromContext={handleRemoveDatasetFromContext}
          onAddAutomationToContext={handleAddAutomationToContext}
          onRemoveAutomationFromContext={handleRemoveAutomationFromContext}
          setIntegrationJobState={setIntegrationJobState}
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