import { TimeSeriesDataset } from '@/types/datasets';
import { format } from 'date-fns';
import { Database, BarChart2, Clock, Layers, Info, X } from 'lucide-react';
import { useState } from 'react';
import TimeSeriesEChart from './TimeSeriesEChart';

interface TimeSeriesVisualizerProps {
  dataset: TimeSeriesDataset;
  onClick?: () => void;
  onClose?: () => void;
}

export function TimeSeriesVisualizerCompact({ dataset, onClick: onExpand }: TimeSeriesVisualizerProps) {
  return (
    <div 
      onClick={onExpand}
      className="bg-[#050a14] rounded-lg p-3 border-2 border-[#101827] hover:border-[#2a4170] hover:bg-[#0a101c] transition-all duration-200 cursor-pointer w-[280px] h-[280px] flex flex-col"
    >
      <div className="flex flex-col gap-1.5 flex-1">
        <div className="flex justify-between items-start">
          <h3 className="text-sm font-medium text-white line-clamp-2 pr-2">{dataset.name}</h3>
          <div className="text-xs text-zinc-500 shrink-0">
            {format(new Date(dataset.updatedAt), 'MMM d')}
          </div>
        </div>
        <p className="text-xs text-zinc-400 flex-1">{dataset.description}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-auto">
        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Database size={14} className="text-blue-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Series</div>
            <div className="text-zinc-300 font-medium">{dataset.numSeries}</div>
          </div>
        </div>
        
        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <BarChart2 size={14} className="text-purple-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Features</div>
            <div className="text-zinc-300 font-medium">{dataset.numFeatures}</div>
          </div>
        </div>

        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Clock size={14} className="text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Timestamps</div>
            <div className="text-zinc-300 font-medium">{dataset.avgNumTimestamps.toFixed(0)}</div>
          </div>
        </div>

        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Layers size={14} className="text-emerald-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Index</div>
            <div className="text-zinc-300 font-medium line-clamp-2">
              {dataset.indexFirstLevel}
              {dataset.indexSecondLevel && `, ${dataset.indexSecondLevel}`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


export function TimeSeriesVisualizerFull({ dataset, onClose }: TimeSeriesVisualizerProps) {
  const [showDescription, setShowDescription] = useState(false);

  return (
    <div className="bg-[#050a14] rounded-lg p-3 border-2 border-[#101827] w-full h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-l text-white">{dataset.name}</h2>
            <button
              onClick={() => setShowDescription(!showDescription)}
              className="text-zinc-400 hover:text-zinc-300 transition-colors"
              title={showDescription ? "Hide description" : "Show description"}
            >
              <Info size={16} />
            </button>
          </div>
          {showDescription && (
            <p className="text-sm text-zinc-400 mt-1">{dataset.description}</p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-zinc-500">
            Updated {format(new Date(dataset.updatedAt), 'MMM d, yyyy')}
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-300 transition-colors"
            title="Close visualization"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Main Visualization Area */}
      <div className="flex-1 bg-[#0a101c] rounded-lg p-2 mb-2">
        <div className="w-full h-full flex items-center justify-center text-zinc-500">
          <TimeSeriesEChart />
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-2">
        <div className="flex items-center gap-2 p-2 bg-[#0a101c] rounded-lg">
          <Database size={16} className="text-blue-400" />
          <div>
            <div className="text-xs text-zinc-500">Series</div>
            <div className="text-sm text-zinc-300 font-medium">{dataset.numSeries}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 p-2 bg-[#0a101c] rounded-lg">
          <BarChart2 size={16} className="text-purple-400" />
          <div>
            <div className="text-xs text-zinc-500">Features</div>
            <div className="text-sm text-zinc-300 font-medium">{dataset.numFeatures}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 p-2 bg-[#0a101c] rounded-lg">
          <Clock size={16} className="text-amber-400" />
          <div>
            <div className="text-xs text-zinc-500">Avg. Timestamps</div>
            <div className="text-sm text-zinc-300 font-medium">{dataset.avgNumTimestamps.toFixed(0)}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 p-2 bg-[#0a101c] rounded-lg">
          <Layers size={16} className="text-emerald-400" />
          <div>
            <div className="text-xs text-zinc-500">Index</div>
            <div className="text-sm text-zinc-300 font-medium">
              {dataset.indexFirstLevel}
              {dataset.indexSecondLevel && `, ${dataset.indexSecondLevel}`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

