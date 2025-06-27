'use client';

import { useDatasets } from '@/hooks/useDatasets';
import { useJobs } from '@/hooks';
import { TimeSeriesDataset } from '@/types/datasets';
import { Job } from '@/types/jobs';
import { Database, Plus, Filter } from 'lucide-react';
import DatasetCompact from '@/components/datasets/DatasetCompact';
import DatasetBeingCreated from '@/components/datasets/DatasetBeingCreated';
import { useMemo, useState } from 'react';
import IntegrationModal from '@/components/datasets/IntegrationModal';
import DatasetCreationModal from '@/components/datasets/DatasetCreationModal';
import AddDatasetModal from '@/components/datasets/AddDatasetModal';

const getDatasetGradient = (index: number) => {
  const gradients = [
    'from-rose-600 via-pink-500 to-purple-400',
    'from-green-600 via-emerald-500 to-teal-400',
    'from-blue-600 via-cyan-500 to-teal-400',
    'from-purple-600 via-pink-600 to-red-500',
    'from-orange-600 via-red-500 to-pink-500',
    'from-indigo-600 via-purple-500 to-pink-400',
    'from-cyan-600 via-blue-500 to-indigo-400',
    'from-emerald-600 via-green-500 to-cyan-400',
    'from-violet-600 via-purple-500 to-fuchsia-400',
    'from-sky-600 via-blue-500 to-indigo-400',
    'from-lime-600 via-green-500 to-emerald-400',
    'from-amber-600 via-orange-500 to-red-400',
    'from-pink-600 via-rose-500 to-red-400',
    'from-blue-600 via-indigo-500 to-purple-400',
    'from-teal-600 via-cyan-500 to-blue-400',
    'from-yellow-600 via-amber-500 to-orange-400',
    'from-red-600 via-pink-500 to-purple-400',
    'from-green-600 via-teal-500 to-cyan-400',
    'from-purple-600 via-violet-500 to-indigo-400',
    'from-orange-600 via-amber-500 to-yellow-400',
    'from-indigo-600 via-blue-500 to-cyan-400',
    'from-pink-600 via-fuchsia-500 to-purple-400',
    'from-emerald-600 via-teal-500 to-blue-400',
    'from-red-600 via-orange-500 to-amber-400',
    'from-cyan-600 via-teal-500 to-emerald-400'
  ];
  return gradients[index % gradients.length];
};

export default function DatasetsPageContent() {
  const { datasets, isLoading, isError } = useDatasets();
  const { jobs: integrationJobs, jobState } = useJobs('integration');
  // const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<TimeSeriesDataset | null>(null);
  const [selectedCreationJobId, setSelectedCreationJobId] = useState<string | null>(null);
  const [showFailedJobs, setShowFailedJobs] = useState(false);
  const [showAddDatasetModal, setShowAddDatasetModal] = useState(false);

  const creationJobs: Job[] = useMemo(() => {
    // all jobs in the dataset jobs that are the only ones running (integrationJobs have len = 1), and the jobs in integrationJobs that do not belong to any dataset
    const datasetJobs = (datasets?.timeSeries?.filter(
      dataset => dataset.integrationJobs.length === 1 && dataset.integrationJobs[0].status !== 'completed') || []).map(dataset => dataset.integrationJobs[0]);
    const notInDatasetJobs = integrationJobs?.filter(job => !datasetJobs.some(datasetJob => datasetJob.id === job.id)) || [];
    const notInDatasetJobsNotCompleted = notInDatasetJobs.filter(job => job.status !== 'completed') || [];
    const allJobs = [...datasetJobs, ...notInDatasetJobsNotCompleted];
    
    const filteredJobs = showFailedJobs ? allJobs : allJobs.filter(job => job.status !== 'failed');
    
    return filteredJobs.sort((a, b) => {
      return new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime();
    });
  }, [integrationJobs, datasets, showFailedJobs]);

  const selectedCreationJob = useMemo(() => {
    return integrationJobs.find(job => job.id === selectedCreationJobId);
  }, [integrationJobs, selectedCreationJobId]); 

  // Sort datasets by createdAt in descending order (most recent first)
  const sortedTimeSeriesDatasets = useMemo(() => {
    const timeSeriesDatasets = datasets?.timeSeries || [];
    return [...timeSeriesDatasets].sort((a, b) => {
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });
  }, [datasets]);

  const handleAddDataset = () => {
    setShowAddDatasetModal(true);
  };

  const toggleFailedJobsFilter = () => {
    setShowFailedJobs(!showFailedJobs);
  };

  // const handleIntegrationStarted = (job: Job) => {
  //   setSelectedDataset(null);
  // };

  if (isLoading) {
    return (
      <div className="flex h-full w-full bg-zinc-950 mt-12">
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-[#101827] bg-[#0a101c]/70 backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <h2 className="text-xs font-mono uppercase tracking-wider text-gray-400">DATASETS</h2>
            </div>
          </div>
          
          {/* Loading Content */}
          <div className="flex-grow p-6 overflow-y-auto">
            <div className="text-center text-zinc-500 pt-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
              <p className="text-xs font-mono text-gray-500">Loading datasets...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full w-full bg-zinc-950 mt-12">
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-[#101827] bg-[#0a101c]/70 backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <h2 className="text-xs font-mono uppercase tracking-wider text-gray-400">DATASETS</h2>
            </div>
          </div>
          
          {/* Error Content */}
          <div className="flex-grow p-6 overflow-y-auto">
            <div className="text-center text-zinc-500 pt-16">
              <Database size={32} className="mx-auto mb-3 opacity-50"/>
              <p className="text-xs font-mono text-gray-400">Error loading datasets</p>
              <p className="text-xs font-mono text-gray-500 mt-1">Please try refreshing the page</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full bg-zinc-950 mt-12">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#101827] backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <h2 className="text-base font-mono uppercase tracking-wider text-gray-400">DATASETS</h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleFailedJobsFilter}
              className={`flex items-center gap-2 px-3 py-2 border rounded-lg transition-all duration-200 text-xs font-medium backdrop-blur-sm ${
                jobState === 'failed' && !showFailedJobs
                  ? 'bg-red-600/20 border-red-500/50 text-red-300 hover:bg-red-600/30 hover:border-red-400/70 hover:text-red-200 animate-pulse'
                  : showFailedJobs 
                    ? 'bg-zinc-800/50 border-zinc-600/50 text-zinc-300 hover:bg-zinc-700/50 hover:border-zinc-500/50'
                    : 'bg-zinc-800/50 border-zinc-600/50 text-zinc-300 hover:bg-zinc-700/50 hover:border-zinc-500/50'
              }`}
            >
              <Filter size={14} />
              {jobState === 'failed' && !showFailedJobs 
                ? 'Job Failed' 
                : showFailedJobs 
                  ? 'Hide Failed' 
                  : 'Show Failed'
              }
            </button>
            <button
              onClick={handleAddDataset}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600/20 to-purple-600/20 hover:from-blue-600/30 hover:to-purple-600/30 border border-blue-500/50 hover:border-blue-400/70 text-blue-300 hover:text-blue-200 rounded-lg transition-all duration-200 text-sm font-medium shadow-lg hover:shadow-blue-500/20 backdrop-blur-sm"
            >
              <Plus size={16} />
              Add Dataset
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-grow p-6 overflow-y-auto">
          {sortedTimeSeriesDatasets.length === 0 && creationJobs.length === 0 ? (
            <div className="text-center text-zinc-500 pt-16">
              <Database size={32} className="mx-auto mb-3 opacity-50"/>
              <p className="text-xs font-mono text-gray-400">No datasets found.</p>
              <p className="text-xs font-mono text-gray-500 mt-1">
                {showFailedJobs 
                  ? 'No datasets or jobs available.' 
                  : 'Ready to integrate your first dataset?'
                }
              </p>
            </div>
          ) : (
            selectedDataset ? (
              <IntegrationModal datasetId={selectedDataset.id} onClose={() => setSelectedDataset(null)} gradientClass={getDatasetGradient(0)} />
            ) : selectedCreationJob ? (
              <DatasetCreationModal job={selectedCreationJob} onClose={() => setSelectedCreationJobId(null)} gradientClass={getDatasetGradient(0)} />
            ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              
              {/* Preliminary datasets for running jobs */}
              {creationJobs.map((job: Job, index: number) => (
                <DatasetBeingCreated
                  key={job.id}
                  job={job}
                  gradientClass={getDatasetGradient(sortedTimeSeriesDatasets.length + index)}
                  defaultView="compact"
                  onClick={() => setSelectedCreationJobId(job.id)}
                />
              ))}
              
              {/* Real datasets */}
              {sortedTimeSeriesDatasets.map((dataset: TimeSeriesDataset, index: number) => (
                <DatasetCompact
                  key={dataset.id}
                  dataset={dataset}
                  gradientClass={getDatasetGradient(index)}
                  onClick={() => setSelectedDataset(dataset)}
                />
              ))}
            </div>
            )
          )}
        </div>
      </div>

      {/* Add Dataset Modal */}
      {showAddDatasetModal && (
        <AddDatasetModal 
          onClose={() => setShowAddDatasetModal(false)} 
          gradientClass={getDatasetGradient(0)} 
        />
      )}
    </div>
  );
} 