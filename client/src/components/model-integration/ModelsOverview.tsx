'use client';

import { useState } from 'react';
import { FilePlus, Github, Package, CheckCircle } from 'lucide-react';
import { Model } from '@/types/model-integration';
import ModelIntegrationJobDetail from './ModelIntegrationJobDetail';
import { useModels } from '@/hooks/useModels';

interface ModelIntegrationOverviewProps {
  setCurrentView: (view: 'overview' | 'add' | 'jobs') => void;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

const getModalityGradient = (modality: string) => {
  switch (modality) {
    case 'time_series':
      return 'from-purple-600 via-pink-600 to-red-500';
    case 'computer_vision':
      return 'from-blue-600 via-cyan-500 to-teal-400';
    case 'nlp':
      return 'from-green-600 via-emerald-500 to-teal-400';
    case 'tabular':
      return 'from-orange-600 via-red-500 to-pink-500';
    case 'audio':
      return 'from-indigo-600 via-purple-500 to-pink-400';
    default:
      return 'from-gray-600 via-gray-500 to-gray-400';
  }
};

export default function ModelsOverview({ setCurrentView }: ModelIntegrationOverviewProps) {
  const [selectedIntegrationId, setSelectedIntegrationId] = useState<string | null>(null);
  
  // Mock data - replace with actual data from API
  const { models } = useModels();

  const handleIntegrationClick = (modelId: string) => {
    setSelectedIntegrationId(modelId);
  };

  const handleBack = () => {
    setSelectedIntegrationId(null);
  };

  if (selectedIntegrationId) {
    const model = models?.find(model => model.id === selectedIntegrationId);
    if (!model) return null;
    
    return (
      <ModelIntegrationJobDetail 
        integrationName={model.name}
        integrationStatus="completed"
        onBack={handleBack}
      />
    );
  }

  return (
    <>
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0">
        <h3 className="text-md font-semibold text-zinc-200">My Models</h3>
      </div>
      <div className="flex-grow p-4 overflow-y-auto">
        {models?.length === 0 ? (
          <div className="text-center text-zinc-500 pt-16">
             <FilePlus size={32} className="mx-auto mb-3 opacity-50"/>
             <p className="font-medium text-zinc-400">No models found.</p>
             <p className="text-sm mt-1">Ready to integrate your first model?</p>
             <button 
                onClick={() => setCurrentView('add')} 
                className="mt-4 text-blue-400 hover:text-blue-300 hover:underline text-sm"
             >
                Click here to integrate a model
             </button>
          </div>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {models?.map((model) => (
              <li key={model.id}>
                <ModelCard 
                  model={model}
                  onClick={() => handleIntegrationClick(model.id)}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

function ModelCard({ model, onClick }: { 
  model: Model;
  onClick: () => void;
}) {
  const gradientClass = getModalityGradient(model.modality.name.toLowerCase().replace(' ', '_'));
  
  return (
    <div 
      className="group relative border-2 border-[#101827] bg-[#050a14] rounded-lg p-6 transition-colors hover:bg-[#0a101c] hover:border-[#1d2d50] cursor-pointer flex flex-col h-full"
      onClick={onClick}
    >
      {/* Subtle gradient overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-lg pointer-events-none`} />
      
      <div className="relative flex-grow flex flex-col">
        <div className="flex items-start gap-3 mb-3">
          <h3 className="font-medium text-white text-lg truncate" title={model.name}>
            {model.name}
          </h3>
          <div className="flex items-center space-x-2 flex-shrink-0">
            {model.source.name.toLowerCase() === 'github' ? (
              <Github size={16} className="text-zinc-400" />
            ) : (
              <Package size={16} className="text-zinc-400" />
            )}
            <CheckCircle size={16} className="text-green-400" />
          </div>
        </div>
        
        <p className="text-sm text-zinc-400 mb-4 line-clamp-2 flex-shrink-0" title={model.description}>
          {model.description}
        </p>
        
        {/* Tasks */}
        <div className="flex flex-wrap gap-1 mb-4 items-start min-h-[40px]">
          {model.tasks.slice(0, 2).map((task, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded-full text-xs text-zinc-300 font-medium"
            >
              {task.name.replace('_', ' ')}
            </span>
          ))}
          {model.tasks.length > 2 && (
            <span className="px-2 py-1 bg-zinc-800/50 border border-zinc-700/50 rounded-full text-xs text-zinc-300 font-medium">
              +{model.tasks.length - 2}
            </span>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="relative mt-6 pt-4 border-t border-[#1a2233] text-xs text-zinc-500 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span>Created: {formatDate(model.created_at)}</span>
        </div>
      </div>
    </div>
  );
} 