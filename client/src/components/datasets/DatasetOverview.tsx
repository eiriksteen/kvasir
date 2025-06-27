import { TimeSeriesDataset } from '@/types/datasets';
import { format } from 'date-fns';
import { Database, BarChart2, Clock, Layers, Calendar, TrendingUp, TrendingDown, FileText } from 'lucide-react';

interface DatasetOverviewProps {
  dataset: TimeSeriesDataset;
}

export default function DatasetOverview({ dataset }: DatasetOverviewProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Description */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <div className="flex items-center gap-2 mb-3">
          <FileText size={16} className="text-zinc-400" />
          <h3 className="text-xs font-mono text-gray-300">Description</h3>
        </div>
        <p className="text-sm text-zinc-400 leading-relaxed">{dataset.description}</p>
      </div>

      {/* Key Statistics */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <h3 className="text-xs font-mono text-gray-300 mb-4">Dataset Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="flex items-center gap-3">
            <Database size={18} className="text-blue-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Time Series</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(dataset.numSeries)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <BarChart2 size={18} className="text-purple-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Features</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(dataset.numFeatures)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Clock size={18} className="text-amber-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Avg. Length</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(dataset.avgNumTimestamps)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Layers size={18} className="text-emerald-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Index</div>
              <div className="text-xs font-mono text-gray-200">
                {dataset.indexFirstLevel}
                {dataset.indexSecondLevel && `, ${dataset.indexSecondLevel}`}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Timestamp Analysis */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <h3 className="text-xs font-mono text-gray-300 mb-4">Timestamp Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center gap-3">
            <TrendingUp size={18} className="text-green-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Longest Series</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(dataset.maxNumTimestamps)} timestamps</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <TrendingDown size={18} className="text-red-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Shortest Series</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(dataset.minNumTimestamps)} timestamps</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Clock size={18} className="text-blue-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Length Range</div>
              <div className="text-xs font-mono text-gray-200">
                {formatNumber(dataset.maxNumTimestamps - dataset.minNumTimestamps)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Timeline */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <div className="flex items-center gap-2 mb-4">
          <Calendar size={16} className="text-zinc-400" />
          <h3 className="text-xs font-mono text-gray-300">Dataset Timeline</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 bg-[#101827] rounded-lg">
            <span className="text-xs font-mono text-gray-500">Created</span>
            <span className="text-xs font-mono text-gray-200">
              {format(new Date(dataset.createdAt), 'MMM d, yyyy')}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-[#101827] rounded-lg">
            <span className="text-xs font-mono text-gray-500">Last Updated</span>
            <span className="text-xs font-mono text-gray-200">
              {format(new Date(dataset.updatedAt), 'MMM d, yyyy')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 