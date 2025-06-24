'use client';

import { Database, Calendar, BarChart3, Clock } from 'lucide-react';
import { useDatasets } from '@/hooks/useDatasets';
import { TimeSeriesDataset } from '@/types/datasets';

interface DatasetsOverviewProps {
  setCurrentView: (view: 'overview' | 'add' | 'jobs') => void;
}

// Helper function to get gradient colors for datasets
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

export default function DatasetsOverview({ setCurrentView }: DatasetsOverviewProps) {
  const { datasets, isLoading, isError } = useDatasets();

  // Helper function to format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Helper function to format numbers with commas
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  if (isLoading) {
    return (
      <>
        <div className="flex items-center justify-between p-4 flex-shrink-0 border-b border-[#101827]">
          <h3 className="text-md font-semibold">My Datasets</h3>
        </div>
        <div className="flex-grow p-4 overflow-y-auto">
          <div className="text-center text-zinc-500 pt-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
            <p className="text-zinc-400">Loading datasets...</p>
          </div>
        </div>
      </>
    );
  }

  if (isError) {
    return (
      <>
        <div className="flex items-center justify-between p-4 flex-shrink-0 border-b border-[#101827]">
          <h3 className="text-md font-semibold">My Datasets</h3>
        </div>
        <div className="flex-grow p-4 overflow-y-auto">
          <div className="text-center text-zinc-500 pt-16">
            <Database size={32} className="mx-auto mb-3 opacity-50"/>
            <p className="font-medium text-zinc-400">Error loading datasets</p>
            <p className="text-sm mt-1">Please try refreshing the page</p>
          </div>
        </div>
      </>
    );
  }

  const timeSeriesDatasets = datasets?.timeSeries || [];

  return (
    <>
      <div className="flex items-center justify-between p-4 flex-shrink-0 border-b border-[#101827]">
        <h3 className="text-md font-semibold">My Datasets</h3>
      </div>
      <div className="flex-grow p-4 overflow-y-auto space-y-3">
        {timeSeriesDatasets.length === 0 ? (
          <div className="text-center text-zinc-500 pt-16">
             <Database size={32} className="mx-auto mb-3 opacity-50"/>
             <p className="font-medium text-zinc-400">No datasets found.</p>
             <p className="text-sm mt-1">Ready to integrate your first dataset?</p>
             <button 
                onClick={() => setCurrentView('add')} 
                className="mt-4 text-blue-400 hover:text-blue-300 hover:underline text-sm"
             >
                Click here to integrate a dataset
             </button>
          </div>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {timeSeriesDatasets.map((dataset: TimeSeriesDataset, index: number) => { 
              const gradientClass = getDatasetGradient(index);
              return (
                <li 
                  key={dataset.id} 
                  className="relative border-2 border-[#101827] bg-[#050a14] rounded-lg p-6 transition-colors hover:bg-[#0a101c] hover:border-[#1d2d50] cursor-pointer flex flex-col group"
                >
                  {/* Subtle gradient overlay */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-lg pointer-events-none`} />
                  
                  <div className="relative flex-grow">
                    <div className="flex items-start gap-3">
                      <h4 className="font-medium text-white text-lg" title={dataset.name}>
                        {dataset.name}
                      </h4>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-900/30 border border-blue-700/50 text-blue-300 flex-shrink-0">
                        Time Series
                      </span>
                    </div>
                    <p className="text-sm text-zinc-400 mt-2 line-clamp-2" title={dataset.description}>
                      {dataset.description}
                    </p>
                  </div>
                  <div className="relative mt-6 pt-4 border-t border-[#1a2233] flex flex-col gap-3 text-xs text-zinc-500">
                    <div className="flex items-center gap-2">
                      <BarChart3 size={14} className="flex-shrink-0" />
                      <span>{formatNumber(dataset.numSeries)} series</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Database size={14} className="flex-shrink-0" />
                      <span>{formatNumber(dataset.numFeatures)} feature(s)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="flex-shrink-0" />
                      <span>~{formatNumber(dataset.avgNumTimestamps)} timestamps</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar size={14} className="flex-shrink-0" />
                      <span>Created {formatDate(dataset.createdAt)}</span>
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