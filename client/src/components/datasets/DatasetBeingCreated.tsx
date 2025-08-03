'use client';

import DatasetMini from './DatasetMini';
import DatasetCompact from './DatasetCompact';
import { TimeSeriesDataset } from '@/types/datasets';
import { Run } from '@/types/runs';

interface DatasetBeingCreatedProps {
  job: Run | undefined;
  gradientClass: string;
  defaultView: 'mini' | 'compact';
  onClick: () => void;
}

// Helper function to create preliminary dataset from integration job
const createPreliminaryDataset = (job?: Run): TimeSeriesDataset => {
  if (!job) {
    // Create a default preliminary dataset when no job exists yet
    const now = new Date().toISOString();
    return {
      id: `preliminary-new`,
      userId: '',
      name: "New Dataset",
      description: "Dataset is being created...",
      numSeries: 0,
      numFeatures: 0,
      avgNumTimestamps: 0,
      maxNumTimestamps: 0,
      minNumTimestamps: 0,
      indexFirstLevel: '',
      createdAt: now,
      updatedAt: now,
      type: "timeSeries",
      integrationJobs: []
    };
  }

  return {
    id: `preliminary-${job.id}`,
    userId: '',
    name: job.jobName || "New Dataset",
    description: "Dataset is being created...",
    numSeries: 0,
    numFeatures: 0,
    avgNumTimestamps: 0,
    maxNumTimestamps: 0,
    minNumTimestamps: 0,
    indexFirstLevel: '',
    createdAt: job.startedAt,
    updatedAt: job.startedAt,
    type: "timeSeries",
    integrationJobs: [job]
  };
};

export default function DatasetBeingCreated({ job, gradientClass, defaultView, onClick }: DatasetBeingCreatedProps) {
  
  // Create preliminary dataset
  const preliminaryDataset = createPreliminaryDataset(job);

  return (
    <>
    {defaultView === 'mini' && <DatasetMini dataset={preliminaryDataset} gradientClass={gradientClass}/>}
    {defaultView === 'compact' && <DatasetCompact dataset={preliminaryDataset} gradientClass={gradientClass} onClick={onClick}/>}
    </>
  );
} 