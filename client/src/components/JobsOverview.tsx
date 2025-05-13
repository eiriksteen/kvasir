'use client';

import { X, Info } from 'lucide-react';
import { Job } from '../types/jobs';
import { getStatusColor } from '../lib/utils';
import { useState } from 'react';
import AnalysisJobDetail from './analysisJobDetail';
import { useAnalysis } from '@/hooks/useAnalysis';

interface JobsOverviewProps {
  job_type: string;
  isOpen: boolean;
  onClose: () => void;
  jobs: Job[];
}

export default function JobsOverview({ job_type, isOpen, onClose, jobs }: JobsOverviewProps) {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const { mutateCurrentAnalysis, analysisJobResults } = useAnalysis();

  if (!isOpen) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    const color = getStatusColor(status);
    return (
      <span className={`
        px-2.5 py-1 
        text-xs font-medium 
        rounded-full 
        ${color}
        bg-opacity-10
        border border-opacity-20
        transition-all duration-200
        capitalize
      `}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  const handleJobClick = (job: Job) => {
    if (job_type.toLowerCase() === "analysis") {
      mutateCurrentAnalysis(analysisJobResults?.analysesJobResults.find(analysis => analysis.jobId === job.id) || null);
      setSelectedJob(job);
    } else {
      setSelectedJob(job);
    }
  };

  const handleBack = () => {
    setSelectedJob(null);
  };

  if (selectedJob) {
    return (
      <AnalysisJobDetail
        jobId={selectedJob.id}
        jobName={selectedJob.id}
        jobStatus={selectedJob.status}
        onBack={handleBack}
        onClose={onClose}
      />
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0" onClick={onClose}></div>
      <div className="relative bg-white dark:bg-gray-900 rounded-lg shadow-lg w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h2 className="text-lg font-semibold">{job_type} Jobs</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-4 max-h-[70vh] overflow-y-auto">
          {jobs.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">No {job_type} jobs found.</p>
          ) : (
            <ul className="space-y-3">
              {jobs.map((job) => (
                <li 
                  key={job.id} 
                  className="border rounded-md p-3 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  onClick={() => handleJobClick(job)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium truncate">{job.id}</span>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(job.status)}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleJobClick(job);
                        }}
                        className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
                      >
                        <Info size={16} />
                      </button>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <div>Started: {formatDate(job.startedAt)}</div>
                    {job.completedAt && <div>Completed: {formatDate(job.completedAt)}</div>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
