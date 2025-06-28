'use client';

import { useState, useEffect, useMemo } from 'react';
import { X, Database, Plus } from 'lucide-react';
import { useDatasets } from '@/hooks/useDatasets';
import { useProject } from '@/hooks/useProject';
import { TimeSeriesDataset } from '@/types/datasets';
import DatasetCompact from '../datasets/DatasetCompact';

interface AddDatasetToProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
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

export default function AddDatasetToProjectModal({ isOpen, onClose, projectId }: AddDatasetToProjectModalProps) {
  const { datasets } = useDatasets();
  const { selectedProject, addDatasetToProject } = useProject(projectId);
  const [isAdding, setIsAdding] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setIsAdding(null);
    }
  }, [isOpen]);

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

  // Filter out datasets that are already in the project
  const availableDatasets = useMemo(() => {
    if (!selectedProject || !datasets?.timeSeries) return [];
    return datasets.timeSeries.filter(dataset => 
      !selectedProject.datasetIds.includes(dataset.id)
    );
  }, [selectedProject, datasets]);

  const handleAddDataset = async (dataset: TimeSeriesDataset) => {
    if (!selectedProject || isAdding === dataset.id) return;
    
    setIsAdding(dataset.id);
    try {
      await addDatasetToProject(dataset.id);
      // Close the modal after successful addition
      onClose();
    } catch (error) {
      console.error('Failed to add dataset to project:', error);
    } finally {
      setIsAdding(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-5xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-6 flex-shrink-0 border-b border-[#101827]">
            <div>
              <h2 className="text-xl font-semibold text-white">Add Dataset to Project</h2>
              <p className="text-sm text-zinc-400 mt-1">
                Click on any dataset below to add it to your project
              </p>
            </div>
          </div>

          <div className="flex-grow p-6 overflow-y-auto">
            {availableDatasets.length === 0 ? (
              <div className="text-center text-zinc-500 pt-16">
                <Database size={48} className="mx-auto mb-4 opacity-50"/>
                <p className="font-medium text-zinc-400 text-lg">No datasets available</p>
                <p className="text-sm mt-2">All your datasets are already in this project</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 auto-rows-fr">
                {availableDatasets.map((dataset: TimeSeriesDataset, index: number) => { 
                  const gradientClass = getDatasetGradient(index);
                  const isCurrentlyAdding = isAdding === dataset.id;
                  
                  return (
                    <div key={dataset.id} className="relative group h-full">
                      {/* Add indicator */}
                      <div className="absolute top-3 right-3 z-10">
                        {isCurrentlyAdding ? (
                          <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Plus size={12} className="text-white" />
                          </div>
                        )}
                      </div>
                      
                      <div className="h-full">
                        <DatasetCompact
                          dataset={dataset}
                          gradientClass={gradientClass}
                          onClick={isCurrentlyAdding ? undefined : () => handleAddDataset(dataset)}
                        />
                      </div>
                      
                      {/* Click hint */}
                      {!isCurrentlyAdding && (
                        <div className="absolute inset-0 bg-blue-600/0 group-hover:bg-blue-600/5 rounded-lg transition-colors pointer-events-none" />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 