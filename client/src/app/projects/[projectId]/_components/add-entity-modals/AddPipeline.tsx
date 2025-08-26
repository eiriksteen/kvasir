'use client';

import { useEffect, useMemo, useState } from 'react';
import { X, Folder, ChevronDown } from 'lucide-react';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';
import { useDatasets } from '@/hooks/useDatasets';
import { useProjectChat } from '@/hooks/useProjectChat';

import { useProject } from '@/hooks/useProject';
import { Dataset } from '@/types/data-objects';

function DatasetListItem({ dataset, isFirst, isInContext }: { dataset: Dataset; isFirst: boolean; isInContext: boolean }) {


  return (
    <div className={`group flex items-center gap-2 p-2 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t' : ''} ${
      isInContext 
        ? 'bg-emerald-500/10 border-b border-emerald-500/20' 
        : 'bg-gray-900/50 border-b border-gray-800 hover:bg-gray-800/50'
    }`}>
      <div className="flex items-center gap-3 min-w-0">
        <h3 className="text-sm font-medium text-gray-200 truncate">
          {dataset.name}
        </h3>
        <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-1 rounded flex-shrink-0">
          {dataset.modality}
        </span>
      </div>
      {isInContext && (
        <span className="text-xs text-emerald-400 font-mono ml-auto">✓</span>
      )}
    </div>
  );
}

interface AddPipelineProps {
  onClose: () => void;
  projectId: UUID;
}

export default function AddPipeline({ onClose, projectId }: AddPipelineProps) {
  const [description, setDescription] = useState('');
  const [isSubmitting] = useState(false);
  const [runSchedule, setRunSchedule] = useState('periodically');
  const [scheduleConfig, setScheduleConfig] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const { datasets } = useDatasets();
  const { 
    datasetsInContext, 
    addDatasetToContext, 
    removeDatasetFromContext 
  } = useAgentContext(projectId);

  const { project } = useProject(projectId);
  const { submitPrompt } = useProjectChat(projectId);

  const datasetsInProject = useMemo(() => {
    return datasets?.filter((dataset: Dataset) => project?.datasetIds.includes(dataset.id));
  }, [datasets, project]);

  useEffect(() => { 
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (isDropdownOpen) {
          setIsDropdownOpen(false);
        } else {
          onClose();
        }
      }
    };

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.dropdown-container')) {
        setIsDropdownOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('click', handleClickOutside);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('click', handleClickOutside);
    };
  }, [onClose, isDropdownOpen]);

  const handleDatasetToggle = (dataset: Dataset) => {
    const isActive = datasetsInContext.some((d: Dataset) => d.id === dataset.id);
    if (isActive) {
      removeDatasetFromContext(dataset);
    } else {
      addDatasetToContext(dataset);
    }
  };

  const handleSubmit = async () => {
    const scheduleText = runSchedule === 'periodically' ? scheduleConfig : runSchedule;
    await submitPrompt(`Create a new pipeline!\n\nDescription: ${description}\n\nSchedule: ${scheduleText}`);
    onClose();
  };

  const runScheduleOptions = [
    { value: 'periodically', label: 'Periodically' },
    { value: 'on-demand', label: 'On Demand' },
    { value: 'on-event', label: 'On Event' }
  ];

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-6">Add Pipeline</h3>
          
          {/* Data Sources */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-200">Datasets</h4>
              <span className="text-xs text-gray-500">
                {datasetsInContext.length} in context
              </span>
            </div>
            
            <div className="overflow-y-auto max-h-[40vh]">
              {datasetsInProject && datasetsInProject.length > 0 ? (
                <div className="grid gap-0">
                  {datasetsInProject.map((dataset: Dataset, index: number) => {
                    const isInContext = datasetsInContext.some((d: Dataset) => d.id === dataset.id);
                    return (
                      <div key={dataset.id} onClick={() => handleDatasetToggle(dataset)}>
                        <DatasetListItem 
                          dataset={dataset} 
                          isFirst={index === 0}
                          isInContext={isInContext}
                        />
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <p className="text-sm">No data sources available</p>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">Click to add/remove from context</p>
          </div>

          {/* Dataset Description */}
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-200 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="The pipeline description."
              className="w-full h-full p-2 bg-gray-900/50 border border-gray-800 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 resize-none text-sm"
            />
          </div>


          {/* Dropdown with Run Schedule options */}
          <div className="mb-4 mt-8">
            <label htmlFor="runSchedule" className="block text-sm font-medium text-gray-200 mb-2">
              Run Schedule
            </label>
            <div className="relative dropdown-container">
              <button
                type="button"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="w-full h-10 flex items-center justify-between px-3 py-2 bg-gray-900/50 border border-gray-800 rounded text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 text-sm"
              >
                <span>{runScheduleOptions.find(option => option.value === runSchedule)?.label}</span>
                <ChevronDown 
                  size={16} 
                  className={`text-gray-400 transition-transform duration-200 ml-2 ${isDropdownOpen ? 'rotate-180' : ''}`}
                />
              </button>
              
              {isDropdownOpen && (
                <div className="absolute z-50 w-full mt-1 bg-gray-900 border border-gray-800 rounded-md shadow-lg max-h-48 overflow-y-auto">
                  {runScheduleOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => {
                        setRunSchedule(option.value);
                        setIsDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm transition-colors duration-200 ${
                        runSchedule === option.value
                          ? 'bg-blue-600/20 text-blue-400'
                          : 'text-gray-200 hover:bg-gray-800/50'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Periodic Schedule Configuration */}
          {runSchedule === 'periodically' && (
            <div className="mb-4">
              <label htmlFor="scheduleConfig" className="block text-sm font-medium text-gray-200 mb-2">
                When to run
              </label>
              <textarea
                id="scheduleConfig"
                value={scheduleConfig}
                onChange={(e) => setScheduleConfig(e.target.value)}
                placeholder="every 6 hours, daily at 2pm, every Monday..."
                className="w-full p-2 bg-gray-900/50 border border-gray-800 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 resize-none text-sm"
              />
            </div>
          )}

          {/* Submit Button */}
          <div className="mt-auto pt-4 border-gray-800">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || datasetsInContext.length === 0 || !description || (runSchedule === 'periodically' && !scheduleConfig)}
              className="w-full h-10 flex items-center justify-center gap-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
            >
              <Folder size={16} />
              {isSubmitting ? 'Creating Pipeline...' : 'Create Pipeline'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 