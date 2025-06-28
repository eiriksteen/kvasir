'use client';

import { Database, Calendar, BarChart3, Clock, Loader2, Pause, Check, X } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { useDatasetIsBeingCreated } from '@/hooks/useDatasets';

interface DatasetProps {
  dataset: TimeSeriesDataset;
  gradientClass: string | undefined;
  onClick?: () => void;
  // if null, click is disabled
  // also remove hovering effect to make it look like a disabled button
}


export default function DatasetCompact({ dataset, gradientClass, onClick }: DatasetProps) {
  const {isBeingCreated, creationJobState} = useDatasetIsBeingCreated(dataset); 
  const isDisabled = !onClick;

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

  return (
        <div
            className={`relative border-2 border-[#101827] bg-[#050a14] rounded-lg p-6 transition-colors flex flex-col group h-full ${
              isDisabled 
                ? 'cursor-default opacity-60' 
                : 'cursor-pointer hover:bg-[#0a101c] hover:border-[#1d2d50]'
            }`}
            onClick={onClick ? onClick : undefined}
        >
            {/* Subtle gradient overlay */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass || ''} opacity-5 rounded-lg pointer-events-none`} />
            
            {/* Loading indicator for being created datasets */}
            {isBeingCreated && (
              <div className="absolute top-4 right-4 z-10">
                {creationJobState === 'running' && <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
                {creationJobState === 'paused' && <Pause className="w-5 h-5 text-blue-400" />}
                {creationJobState === 'awaiting_approval' && <Check className="w-5 h-5 text-blue-400" />}
                {creationJobState === 'failed' && <X className="w-5 h-5 text-red-400" />}
              </div>
            )}
            
            <div className="relative flex-grow flex flex-col">
            <div className="flex items-start gap-3">
                <h4 className="font-mono text-gray-200 text-base" title={dataset.name}>
                {dataset.name}
                </h4>
                <span className="px-2 py-1 text-xs font-mono rounded-full bg-blue-900/30 border border-blue-700/50 text-blue-300 flex-shrink-0">
                Time Series
                </span>
            </div>
            <p className="text-sm text-zinc-400 mt-2 line-clamp-2 flex-grow" title={dataset.description}>
                {dataset.description}
            </p>
            </div>
            <div className="relative mt-6 pt-4 border-t border-[#1a2233] flex flex-col gap-3 text-xs font-mono text-gray-500">
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
        </div>
  );
} 