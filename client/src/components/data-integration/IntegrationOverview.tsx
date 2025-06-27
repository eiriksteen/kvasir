'use client';

import { useState } from 'react';
import { FilePlus } from 'lucide-react';
import { useJobs } from '@/hooks';
import { getStatusColor } from '@/lib/utils';
import { Job } from '@/types/jobs';
import IntegrationJobDetail from './IntegrationJobDetail';

interface IntegrationOverviewProps {
  setCurrentView: (view: 'overview' | 'add' | 'jobs') => void;
}

export default function IntegrationOverview({ setCurrentView }: IntegrationOverviewProps) {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const { jobs } = useJobs('integration'); 

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
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0">
        <h3 className="text-md font-semibold text-zinc-200">Jobs Overview</h3>
      </div>
      <div className="flex-grow p-4 overflow-y-auto space-y-3">
        {jobs.length === 0 ? (
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