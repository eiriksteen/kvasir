'use client';

import { useState } from 'react';
// import Link from 'next/link'; // Removed unused import
import { Loader2, AlertTriangle, FilePlus, Plus, Minus } from 'lucide-react';
import { useJobs } from '@/hooks'; // Import useJobs
import { getStatusColor } from '@/lib/utils'; // Import getStatusColor
import { Job } from '@/types/jobs';
import IntegrationJobDetail from './IntegrationJobDetail';
import { useProject } from '@/hooks/useProject';

interface IntegrationOverviewProps {
  // Remove props related to jobs data and helpers
  setCurrentView: (view: 'overview' | 'add') => void;
}

export default function IntegrationOverview({ setCurrentView }: IntegrationOverviewProps) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const { jobs, isLoading, error } = useJobs('integration'); // Use useJobs hook here
  const { selectedProject, updateSelectedProject } = useProject();

  // Define helper functions locally
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    const baseColor = getStatusColor(status);
    const textColor = baseColor.includes('green') ? 'text-green-300'
                     : baseColor.includes('blue') ? 'text-blue-300'
                     : baseColor.includes('yellow') ? 'text-yellow-300'
                     : baseColor.includes('red') ? 'text-red-300'
                     : 'text-zinc-300';
    const bgColor = baseColor.includes('green') ? 'bg-green-900/30 border-green-700/50'
                    : baseColor.includes('blue') ? 'bg-blue-900/30 border-blue-700/50'
                    : baseColor.includes('yellow') ? 'bg-yellow-900/30 border-yellow-700/50'
                    : baseColor.includes('red') ? 'bg-red-900/30 border-red-700/50'
                    : 'bg-zinc-700/30 border-zinc-600/50';

    return (
      <span className={`
        px-2 py-0.5 text-xs font-medium rounded-full border capitalize whitespace-nowrap
        ${bgColor} ${textColor}
      `}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  const handleJobClick = (jobId: string) => {
    setSelectedJobId(jobId);
  };

  const handleAddToProject = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    if (!selectedProject) return;
    
    await updateSelectedProject({
      type: "dataset",
      id: jobId,
      remove: false,
    });
  };

  const handleRemoveFromProject = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    if (!selectedProject) return;
    
    await updateSelectedProject({
      type: "dataset",
      id: jobId,
      remove: true,
    });
  };

  const handleBack = () => {
    setSelectedJobId(null);
  };

  if (selectedJobId) {
    return (
      <IntegrationJobDetail 
        jobId={selectedJobId} 
        jobName={jobs.find(job => job.id === selectedJobId)?.jobName || ''}
        jobStatus={jobs.find(job => job.id === selectedJobId)?.status || ''}
        onBack={handleBack}
      />
    );
  }

  return (
    <>
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0 bg-[#050a14]/50">
        <h3 className="text-md font-semibold text-zinc-200">Jobs Overview</h3>
      </div>
      <div className="flex-grow p-4 overflow-y-auto space-y-3">
        {isLoading ? (
          <div className="flex justify-center items-center h-full text-zinc-500">
             <Loader2 size={20} className="animate-spin mr-2" /> Loading jobs...
          </div>
        ) : error ? (
          <div className="text-center text-red-400 pt-10 flex flex-col items-center">
             <AlertTriangle size={24} className="mb-2"/>
             <p>Error loading jobs:</p>
             <p className="text-sm text-red-500">{error.message}</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center text-zinc-500 pt-16">
             <FilePlus size={32} className="mx-auto mb-3 opacity-50"/>
             <p className="font-medium text-zinc-400">No integration jobs found.</p>
             <p className="text-sm mt-1">Ready to integrate your first dataset?</p>
             <button 
                onClick={() => setCurrentView('add')} 
                className="mt-4 text-blue-400 hover:text-blue-300 hover:underline text-sm"
             >
                Click here to add a dataset
             </button>
          </div>
        ) : (
          <ul className="space-y-3">
            {jobs.map((job: Job) => { 
              const isInProject = selectedProject?.datasetIds.includes(job.id);
              const showProjectButton = job.status === "completed" && selectedProject;
              console.log("jobs", jobs);
              return (
                <li 
                  key={job.id} 
                  className="border-2 border-[#101827] bg-[#050a14] rounded-lg transition-colors hover:bg-[#0a101c] hover:border-[#1d2d50] cursor-pointer"
                  onClick={() => handleJobClick(job.id)}
                >
                 <div className="p-3">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="font-mono text-sm text-white-400 truncate mr-4" title={job.jobName}>{job.jobName}</span>
                      {getStatusBadge(job.status)}
                    </div>
                    <div className="flex justify-between items-center">
                      <div className="text-xs text-zinc-500 space-y-0.5">
                        <span>Started: {formatDate(job.startedAt)}</span>
                        {job.completedAt && <span className="block">Completed: {formatDate(job.completedAt)}</span>}
                      </div>
                      {showProjectButton && (
                        isInProject ? (
                          <button
                            onClick={(e) => handleRemoveFromProject(e, job.id)}
                            className="px-3 py-1 rounded-md bg-red-500 text-white hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700 text-sm flex items-center gap-1"
                            title="Remove from project"
                          >
                            <Minus size={14} />
                            Remove from project
                          </button>
                        ) : (
                          <button
                            onClick={(e) => handleAddToProject(e, job.id)}
                            className="px-3 py-1 rounded-md bg-blue-500 text-white hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 text-sm flex items-center gap-1"
                            title="Add to project"
                          >
                            <Plus size={14} />
                            Add to project
                          </button>
                        )
                      )}
                    </div>
                 </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </>
  );
} 