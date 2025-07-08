import { Model } from '@/types/model-integration';
import { format } from 'date-fns';
import { X } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import ModelOverview from './ModelOverview';
import { useModelIsBeingCreated } from '@/hooks/useModels';

type View = 'overview' | 'integration';

interface ModelFullProps {
  model: Model;
  onClose: () => void;
  gradientClass: string | undefined;
}

export default function ModelFull({ model, onClose, gradientClass }: ModelFullProps) {
  const {isBeingCreated} = useModelIsBeingCreated(model);
  const [currentView, setCurrentView] = useState<View>('overview');

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

  if (!model) return null;

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
            <h2 className="text-base font-mono text-gray-200">{model.name}</h2>
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
                title={isBeingCreated ? "Not available while creating model" : "Overview"}
              >
                Overview
              </button>
              <button
                onClick={() => setCurrentView('integration')}
                disabled={isBeingCreated}
                className={`px-3 py-1.5 text-xs font-mono rounded-md transition-colors ${
                  currentView === 'integration'
                    ? 'bg-blue-600 text-white'
                    : isBeingCreated
                      ? 'text-zinc-600 cursor-not-allowed'
                      : 'text-zinc-400 hover:text-zinc-300'
                }`}
                title={isBeingCreated ? "Not available while creating model" : "Integration"}
              >
                Integration
              </button>
            </div>
            
            <div className="text-xs font-mono text-gray-500 ml-4">
              Created {format(new Date(model.createdAt), 'MMM d, yyyy')}
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
            {currentView === 'overview' && <ModelOverview model={model} />}
            {currentView === 'integration' && (
              <div className="flex flex-col justify-center items-center h-full text-zinc-500">
                <p className="text-sm">Model integration details will be available here.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}


