'use client';

import { X } from 'lucide-react';
import { Job } from '../types/jobs';

interface JobsOverviewProps {
  job_type: string;
  isOpen: boolean;
  onClose: () => void;
  jobs: Job[];
}

export default function JobsOverview({ job_type, isOpen, onClose, jobs }: JobsOverviewProps) {
  if (!isOpen) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'in_progress':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-200 text-yellow-800">In Progress</span>;
      case 'failed':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-200 text-red-800">Failed</span>;
      case 'completed':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-200 text-green-800">Completed</span>;
      default:
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-200 text-gray-800">{status}</span>;
    }
  };

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
                <li key={job.id} className="border rounded-md p-3 dark:border-gray-700">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium truncate">{job.id}</span>
                    {getStatusBadge(job.status)}
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
