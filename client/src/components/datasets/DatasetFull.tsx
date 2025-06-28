import { TimeSeriesDataset, EntityMetadata } from '@/types/datasets';
import { format } from 'date-fns';
import { X, ArrowLeft } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import TimeSeriesEChart from '@/components/data-visualization/TimeSeriesEChart';
import DatasetOverview from './DatasetOverview';
import DatasetDataView from './DatasetDataView';
import { useDatasetIsBeingCreated } from '@/hooks/useDatasets';

type View = 'overview' | 'data';

interface DatasetFullProps {
  dataset: TimeSeriesDataset;
  entities: EntityMetadata[] | undefined;
  onClose: () => void;
  gradientClass: string | undefined;
}

export default function DatasetFull({ dataset, entities, onClose, gradientClass }: DatasetFullProps) {
  const {isBeingCreated} = useDatasetIsBeingCreated(dataset);
  const [currentView, setCurrentView] = useState<View>(isBeingCreated ? 'overview' : 'overview');
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [navigationHistory, setNavigationHistory] = useState<string[]>([]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle escape key to close modal
  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleEscape, true);
    return () => document.removeEventListener('keydown', handleEscape, true);
  }, [handleEscape]);

  if (!dataset) return null;

  const selectedEntity = entities?.find(e => e.entityId === selectedEntityId);

  const handleEntitySelect = (entityId: string) => {
    setSelectedEntityId(entityId);
    setNavigationHistory(prev => [...prev, entityId]);
  };

  const handleBack = () => {
    // If we're in data view with a selected entity, go back to entity list
    if (currentView === 'data' && selectedEntityId) {
      const newHistory = [...navigationHistory];
      newHistory.pop();
      const previousEntityId = newHistory[newHistory.length - 1] || null;
      setSelectedEntityId(previousEntityId);
      setNavigationHistory(newHistory);
      return;
    }
  };

  // Check if back button should be enabled
  const canGoBack = () => {
    if (currentView === 'data' && selectedEntityId) return true;
    return false;
  };

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="relative bg-[#050a14] rounded-xl p-6 border-2 border-[#101827] w-full max-w-6xl h-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          {gradientClass && (
            <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-xl pointer-events-none`} />
          )}
          
          <div className="relative flex items-center gap-2 mb-4">
            <button
              onClick={handleBack}
              disabled={!canGoBack()}
              className={`transition-colors ${
                canGoBack() 
                  ? 'text-zinc-400 hover:text-zinc-300' 
                  : 'text-zinc-600 cursor-not-allowed'
              }`}
              title={
                currentView === 'data' && selectedEntityId 
                  ? "Back to entities"
                  : "No back navigation available"
              }
            >
              <ArrowLeft size={20} />
            </button>
            <h2 className="text-base font-mono text-gray-200">{dataset.name}</h2>
            <div className="flex-1" />
            
            {/* Navigation Tabs */}
            <div className="flex items-center gap-1 bg-[#0a101c] rounded-lg p-1 border border-[#1a2234]">
              <button
                onClick={() => setCurrentView('overview')}
                disabled={isBeingCreated}
                className={`px-3 py-1.5 text-xs font-mono rounded-md transition-colors ${
                  currentView === 'overview'
                    ? 'bg-blue-600 text-white'
                    : isBeingCreated
                      ? 'text-zinc-600 cursor-not-allowed'
                      : 'text-zinc-400 hover:text-zinc-300'
                }`}
                title={isBeingCreated ? "Not available while creating dataset" : "Overview"}
              >
                Overview
              </button>
              <button
                onClick={() => setCurrentView('data')}
                disabled={isBeingCreated}
                className={`px-3 py-1.5 text-xs font-mono rounded-md transition-colors ${
                  currentView === 'data'
                    ? 'bg-blue-600 text-white'
                    : isBeingCreated
                      ? 'text-zinc-600 cursor-not-allowed'
                      : 'text-zinc-400 hover:text-zinc-300'
                }`}
                title={isBeingCreated ? "Not available while creating dataset" : "Data"}
              >
                Data
              </button>
            </div>
            
            <div className="text-xs font-mono text-gray-500 ml-4">
              Updated {format(new Date(dataset.updatedAt), 'MMM d, yyyy')}
            </div>
            <button
              onClick={onClose}
              className="text-zinc-400 hover:text-zinc-300 transition-colors ml-2"
              title="Close visualization"
            >
              <X size={20} />
            </button>
          </div>
          
          {/* Main Content */}
          <div className="relative flex-1 min-h-0">
            {currentView === 'overview' && <DatasetOverview dataset={dataset} />}
            {currentView === 'data' && (
              selectedEntityId && selectedEntity ? (
                <TimeSeriesEChart 
                  entityId={selectedEntityId}
                  entity={selectedEntity}
                />
              ) : (
                <DatasetDataView 
                  entities={entities}
                  onEntitySelect={handleEntitySelect}
                />
              )
            )}
          </div>
        </div>
      </div>
    </>
  );
}


