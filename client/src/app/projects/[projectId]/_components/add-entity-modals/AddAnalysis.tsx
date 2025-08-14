'use client';

import { useState, useEffect, useMemo } from 'react';
import { X, Info } from 'lucide-react';
import { useProject } from '@/hooks/useProject';
import { useDatasets } from '@/hooks';
import { Dataset } from '@/types/data-objects';

interface AddAnalysisProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function AddAnalysis({ projectId, isOpen, onClose }: AddAnalysisProps) {
  const [requirements, setRequirements] = useState('');
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>([]);
  const { selectedProject } = useProject(projectId);
  const { datasets } = useDatasets();

  // Filter datasets based on selected project
  const filteredDatasets = useMemo(() => {
    if (!selectedProject || !datasets) return [];
    return datasets.filter((dataset: Dataset) => 
      selectedProject.datasetIds.includes(dataset.id)
    );
  }, [selectedProject, datasets]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    } else {
      window.removeEventListener('keydown', handleKeyDown);
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleDatasetToggle = (datasetId: string) => {
    setSelectedDatasets(prev => 
      prev.includes(datasetId)
        ? prev.filter(id => id !== datasetId)
        : [...prev, datasetId]
    );
  };

  const handleSubmit = () => {
    // TODO: Implement analysis submission
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative flex w-full max-w-5xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex-1 flex flex-col p-6 overflow-hidden bg-gray-950">
          <h2 className="text-xl font-semibold text-white mb-6">Create New Analysis</h2>
          
          <div className="space-y-6 flex-grow overflow-y-auto">
            <div>
              <label htmlFor="requirements" className="block text-sm font-medium text-zinc-400 mb-2">
                Analysis Requirements
              </label>
              <textarea
                id="requirements"
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                className="w-full h-32 px-4 py-3 bg-[#0a101c] border border-[#1d2d50] rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-[#2a4170]"
                placeholder="Describe what you want to analyze..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">
                Select Datasets
              </label>
              <div className="space-y-2">
                {filteredDatasets.map((dataset) => (
                  <label
                    key={dataset.id}
                    className="flex items-center space-x-3 p-3 bg-[#0a101c] border border-[#1d2d50] rounded-lg cursor-pointer hover:bg-[#111827]"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDatasets.includes(dataset.id)}
                      onChange={() => handleDatasetToggle(dataset.id)}
                      className="h-4 w-4 text-[#2a4170] border-[#1d2d50] rounded focus:ring-[#2a4170]"
                    />
                    <span className="text-white">{dataset.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div className="p-3 rounded-lg bg-[#111827] border border-[#1a2438]">
              <h3 className="text-xs font-medium text-[#6b89c0] mb-1.5 flex items-center">
                <Info size={12} className="mr-1.5 flex-shrink-0"/>
                Tip
              </h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Remember, you can always ask simple questions of the data in the chat to the right. This analysis is meant for more complex questions that requires several steps to solve.
              </p>
            </div>

            <button
              onClick={handleSubmit}
              className="w-full px-4 py-2 bg-[#2a4170] text-white rounded-lg hover:bg-[#1d2d50] transition-colors"
            >
              Create Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
