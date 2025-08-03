'use client';

import ModelMini from './ModelMini';
import ModelCompact from './ModelCompact';
import { Model } from '@/types/model-integration';
import { Run } from '@/types/runs';

interface ModelBeingCreatedProps {
  job: Run | undefined;
  gradientClass: string;
  defaultView: 'mini' | 'compact';
  onClick: () => void;
}

// Helper function to create preliminary model from integration job
const createPreliminaryModel = (job?: Run): Model => {
  if (!job) {
    // Create a default preliminary model when no job exists yet
    const now = new Date().toISOString();
    return {
      id: `preliminary-new`,
      name: "New Model",
      description: "Model is being created...",
      inputDescription: "Input description will be available once the model is created",
      outputDescription: "Output description will be available once the model is created",
      modality: { id: "unknown", name: "Unknown" },
      source: { id: "unknown", name: "Unknown", createdAt: now },
      programmingLanguageVersion: { id: "unknown", programmingLanguageId: "unknown", version: "unknown", createdAt: now },
      tasks: [],
      configParameters: [],
      createdAt: now,
      public: false,
      integrationJobs: []
    };
  }

  return {
    id: `preliminary-${job.id}`,
    name: "New Model",
    description: "Model is being created...",
    inputDescription: "Input description will be available once the model is created",
    outputDescription: "Output description will be available once the model is created",
    modality: { id: "unknown", name: "Unknown" },
    source: { id: "unknown", name: "Unknown", createdAt: job.startedAt },
    programmingLanguageVersion: { id: "unknown", programmingLanguageId: "unknown", version: "unknown", createdAt: job.startedAt },
    tasks: [],
    configParameters: [],
    createdAt: job.startedAt,
    public: false,
    integrationJobs: [job]
  };
};

export default function ModelBeingCreated({ job, gradientClass, defaultView, onClick }: ModelBeingCreatedProps) {
  
  // Create preliminary model
  const preliminaryModel = createPreliminaryModel(job);

  return (
    <>
    {defaultView === 'mini' && <ModelMini model={preliminaryModel} gradientClass={gradientClass}/>}
    {defaultView === 'compact' && <ModelCompact model={preliminaryModel} gradientClass={gradientClass} onClick={onClick}/>}
    </>
  );
} 