'use client';

import { useState, useEffect, useMemo } from 'react';
import { X, Database, Plus, Calendar, BarChart3, Clock } from 'lucide-react';
import { useDatasets } from '@/hooks/useDatasets';
import { useProject } from '@/hooks/useProject';
import { TimeSeriesDataset } from '@/types/datasets';

interface AddDatasetToProjectProps {
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

export default function AddDatasetToProject({ isOpen, onClose, projectId }: AddDatasetToProjectProps) {
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
              <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {availableDatasets.map((dataset: TimeSeriesDataset, index: number) => { 
                  const gradientClass = getDatasetGradient(index);
                  const isCurrentlyAdding = isAdding === dataset.id;
                  
                  return (
                    <li 
                      key={dataset.id} 
                      onClick={() => handleAddDataset(dataset)}
                      className={`relative border-2 border-[#101827] bg-[#050a14] rounded-lg p-4 transition-all duration-200 cursor-pointer flex flex-col group ${
                        isCurrentlyAdding 
                          ? 'border-blue-500 bg-blue-900/20 cursor-not-allowed' 
                          : 'hover:bg-[#0a101c] hover:border-[#1d2d50] hover:scale-[1.02]'
                      }`}
                    >
                      {/* Subtle gradient overlay */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-lg pointer-events-none`} />
                      
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
                      
                      <div className="relative flex-grow">
                        <div className="flex items-start gap-2">
                          <h4 className="font-medium text-white text-base" title={dataset.name}>
                            {dataset.name}
                          </h4>
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-900/30 border border-blue-700/50 text-blue-300 flex-shrink-0">
                            Time Series
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400 mt-2 line-clamp-2" title={dataset.description}>
                          {dataset.description || 'No description available'}
                        </p>
                      </div>
                      
                      <div className="relative mt-4 pt-3 border-t border-[#1a2233] flex flex-col gap-2 text-xs text-zinc-500">
                        <div className="flex items-center gap-2">
                          <BarChart3 size={12} className="flex-shrink-0" />
                          <span>{formatNumber(dataset.numSeries)} series</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Database size={12} className="flex-shrink-0" />
                          <span>{formatNumber(dataset.numFeatures)} feature(s)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock size={12} className="flex-shrink-0" />
                          <span>~{formatNumber(dataset.avgNumTimestamps)} timestamps</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar size={12} className="flex-shrink-0" />
                          <span>Created {formatDate(dataset.createdAt)}</span>
                        </div>
                      </div>
                      
                      {/* Click hint */}
                      {!isCurrentlyAdding && (
                        <div className="absolute inset-0 bg-blue-600/0 group-hover:bg-blue-600/5 rounded-lg transition-colors pointer-events-none" />
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 