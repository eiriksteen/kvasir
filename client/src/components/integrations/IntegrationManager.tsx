'use client';

import { useState, useEffect } from 'react';
import { X, List, FilePlus, Info } from 'lucide-react';
import IntegrationOverview from './IntegrationOverview';
import AddDataset from './AddDataset';

interface IntegrationManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

type View = 'overview' | 'add';

export default function IntegrationManager({ isOpen, onClose }: IntegrationManagerProps) {
  const [currentView, setCurrentView] = useState<View>('overview');

  useEffect(() => {
      if (!isOpen) {
         setCurrentView('overview');
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

        <div className="w-60 flex-shrink-0 bg-[#050a14] border-r border-[#101827] p-4 flex flex-col">
           <h2 className="text-sm font-mono uppercase tracking-wider text-[#6b89c0] mb-6">Integrations</h2>
           <nav className="space-y-2 flex-grow">
              <button
                onClick={() => setCurrentView('overview')}
                className={`w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors border-2 ${
                  currentView === 'overview' 
                    ? 'bg-[#0a101c] border-[#2a4170] text-white' 
                    : 'text-zinc-400 bg-[#050a14] border-[#101827] hover:bg-[#0a101c] hover:border-[#1d2d50] hover:text-zinc-200'
                }`}
              >
                <List size={16} className="mr-3" />
                Overview
              </button>
              <button
                onClick={() => setCurrentView('add')}
                className={`w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors border-2 ${
                  currentView === 'add' 
                    ? 'bg-[#0a101c] border-[#2a4170] text-white' 
                    : 'text-zinc-400 bg-[#050a14] border-[#101827] hover:bg-[#0a101c] hover:border-[#1d2d50] hover:text-zinc-200'
                }`}
              >
                 <FilePlus size={16} className="mr-3" />
                Add Dataset
              </button>
           </nav>

            <div className="mt-auto mb-4 p-3 rounded-lg bg-[#111827] border border-[#1a2438]">
                <h3 className="text-xs font-medium text-[#6b89c0] mb-1.5 flex items-center">
                    <Info size={12} className="mr-1.5 flex-shrink-0"/>
                    Tip
                </h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                    Select an integration job to view its progress and monitor everything the AI is doing.
                </p>
            </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden bg-gray-950">
          {currentView === 'overview' && (
            <IntegrationOverview
              setCurrentView={setCurrentView}
            />
          )}

          {currentView === 'add' && (
            <AddDataset
              setCurrentView={setCurrentView}
            />
          )}
        </div>
      </div>
    </div>
  );
} 