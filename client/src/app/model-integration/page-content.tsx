'use client';

import { useState } from 'react';
import ModelsOverview from '@/components/model-integration/ModelsOverview';
import AddModel from '@/components/model-integration/AddModel';
import ModelIntegrationOverview from '@/components/model-integration/ModelIntegrationOverview';
import { Brain, FilePlus, List, Info } from 'lucide-react';

type View = 'overview' | 'add' | 'jobs';

export default function ModelIntegrationPageContent() {
  const [currentView, setCurrentView] = useState<View>('overview');

  return (
    <div className="flex h-full w-full bg-zinc-950 mt-12">
      <div className="w-60 flex-shrink-0 bg-[#050a14] border-r border-[#101827] p-4 flex flex-col">
        <h2 className="text-sm font-mono uppercase tracking-wider text-[#6b89c0] mb-6">Model Integrations</h2>
        <nav className="space-y-2 flex-grow">
          <button
            onClick={() => setCurrentView('overview')}
            className={`w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors border-2 ${
              currentView === 'overview' 
                ? 'bg-[#0a101c] border-[#2a4170] text-white' 
                : 'text-zinc-400 bg-[#050a14] border-[#101827] hover:bg-[#0a101c] hover:border-[#1d2d50] hover:text-zinc-200'
            }`}
          >
            <Brain size={16} className="mr-3" />
            My Models
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
            Integrate Model
          </button>
          <button
            onClick={() => setCurrentView('jobs')}
            className={`w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors border-2 ${
              currentView === 'jobs' 
                ? 'bg-[#0a101c] border-[#2a4170] text-white' 
                : 'text-zinc-400 bg-[#050a14] border-[#101827] hover:bg-[#0a101c] hover:border-[#1d2d50] hover:text-zinc-200'
            }`}
          >
            <List size={16} className="mr-3" />
            Integration Jobs
          </button>
        </nav>

        <div className="mt-auto mb-4 p-3 rounded-lg bg-[#111827] border border-[#1a2438]">
          <h3 className="text-xs font-medium text-[#6b89c0] mb-1.5 flex items-center">
            <Info size={12} className="mr-1.5 flex-shrink-0"/>
            Tip
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            View your models, integrate new AI models, or monitor integration job progress.
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {currentView === 'overview' && (
          <ModelsOverview
            setCurrentView={setCurrentView}
          />
        )}

        {currentView === 'add' && (
          <AddModel
            setCurrentView={setCurrentView}
          />
        )}

        {currentView === 'jobs' && (
          <ModelIntegrationOverview
            setCurrentView={setCurrentView}
          />
        )}
      </div>
    </div>
  );
} 