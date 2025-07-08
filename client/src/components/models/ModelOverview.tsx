import { Model } from '@/types/model-integration';
import { format } from 'date-fns';
import { Target, Settings, Calendar, Layers, FileText, Code, Zap } from 'lucide-react';

interface ModelOverviewProps {
  model: Model;
}

export default function ModelOverview({ model }: ModelOverviewProps) {
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
        <p className="text-sm text-zinc-400 leading-relaxed">{model.description}</p>
      </div>

      {/* Model Information */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <h3 className="text-xs font-mono text-gray-300 mb-4">Model Information</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="flex items-center gap-3">
            <Layers size={18} className="text-blue-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Modality</div>
              <div className="text-xs font-mono text-gray-200">{model.modality.name}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Target size={18} className="text-purple-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Tasks</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(model.tasks.length)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Settings size={18} className="text-amber-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Config Params</div>
              <div className="text-xs font-mono text-gray-200">{formatNumber(model.configParameters.length)}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Code size={18} className="text-emerald-400" />
            <div>
              <div className="text-xs font-mono text-gray-500">Type</div>
              <div className="text-xs font-mono text-gray-200">Time Series</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tasks Overview */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <h3 className="text-xs font-mono text-gray-300 mb-4">Tasks</h3>
        <div className="space-y-3">
          {model.tasks.map((task, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-[#101827] rounded-lg">
              <Zap size={16} className="text-blue-400" />
              <div>
                <div className="text-xs font-mono text-gray-200">{task.name}</div>
                <div className="text-xs font-mono text-gray-500">{task.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Model Timeline */}
      <div className="bg-[#0a101c] rounded-lg p-6 border border-[#1a2234] shadow-sm flex-1 flex flex-col justify-center">
        <div className="flex items-center gap-2 mb-4">
          <Calendar size={16} className="text-zinc-400" />
          <h3 className="text-xs font-mono text-gray-300">Model Timeline</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 bg-[#101827] rounded-lg">
            <span className="text-xs font-mono text-gray-500">Created</span>
            <span className="text-xs font-mono text-gray-200">
              {format(new Date(model.createdAt), 'MMM d, yyyy')}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-[#101827] rounded-lg">
            <span className="text-xs font-mono text-gray-500">Last Updated</span>
            <span className="text-xs font-mono text-gray-200">
              {format(new Date(model.createdAt), 'MMM d, yyyy')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 