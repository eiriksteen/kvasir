'use client';

import { useState } from 'react';
import { Plus, Github, Package, CheckCircle, Clock, Play, AlertCircle, FilePlus } from 'lucide-react';
import { ModelIntegration } from '@/types/model-integration';

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return <CheckCircle size={16} className="text-green-400" />;
    case 'running': return <Play size={16} className="text-blue-400" />;
    case 'failed': return <AlertCircle size={16} className="text-red-400" />;
    default: return <Clock size={16} className="text-yellow-400" />;
  }
};

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

export default function ModelIntegrationManager() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [integrations, setIntegrations] = useState<ModelIntegration[]>([
    // Time Series Models
    {
      id: '1',
      name: 'XGBoost',
      source: 'pip',
      url: 'xgboost',
      status: 'completed',
      progress: 100,
      startedAt: '2024-01-15T10:30:00Z',
      completedAt: '2024-01-15T11:45:00Z',
      tasks: ['time_series_forecasting'],
      modality: 'time_series'
    },
    // NLP Models
    {
      id: '10',
      name: 'GPT-2',
      source: 'github',
      url: 'https://github.com/openai/gpt-2',
      status: 'completed',
      progress: 100,
      startedAt: '2024-01-14T15:00:00Z',
      completedAt: '2024-01-14T16:45:00Z',
      tasks: ['text_generation', 'language_modeling'],
      modality: 'nlp'
    }
  ]);

  const handleAddIntegration = (formData: { source: 'github' | 'pip'; url: string }) => {
    const tasks = formData.source === 'github' 
      ? ['time_series_forecasting', 'classification'] 
      : ['classification', 'regression'];
    
    const modality = formData.source === 'github' ? 'time_series' : 'tabular';
    
    // Extract name from URL
    const name = formData.source === 'github' 
      ? formData.url.split('/').pop() || 'Unknown Model'
      : formData.url;

    const newIntegration: ModelIntegration = {
      ...formData,
      name,
      id: Date.now().toString(),
      status: 'pending',
      progress: 0,
      startedAt: new Date().toISOString(),
      tasks,
      modality
    };
    
    setIntegrations(prev => [newIntegration, ...prev]);
    setShowAddForm(false);
  };

  // Group integrations by modality
  const groupedIntegrations = integrations.reduce((acc, integration) => {
    const modality = integration.modality;
    if (!acc[modality]) {
      acc[modality] = [];
    }
    acc[modality].push(integration);
    return acc;
  }, {} as Record<string, ModelIntegration[]>);

  const modalityOrder = ['time_series', 'computer_vision', 'nlp', 'tabular', 'audio'];

  return (
    <div className="h-full flex flex-col bg-[#050a14]">
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0 bg-[#050a14]/50">
        <h3 className="text-md font-semibold text-zinc-200">Model Integrations</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center px-3 py-1.5 bg-[#2a4170] hover:bg-[#1d2d50] text-white rounded-lg transition-colors text-sm"
        >
          <Plus size={14} className="mr-2" />
          Add Model
        </button>
      </div>

      <div className="flex-grow p-4 overflow-y-auto">
        {showAddForm ? (
          <AddModelForm onSubmit={handleAddIntegration} onCancel={() => setShowAddForm(false)} />
        ) : (
          <div className="space-y-6">
            {Object.keys(groupedIntegrations).length === 0 ? (
              <div className="text-center text-zinc-500 pt-16">
                <FilePlus size={32} className="mx-auto mb-3 opacity-50"/>
                <p className="font-medium text-zinc-400">No model integrations found.</p>
                <p className="text-sm mt-1">Ready to integrate your first model?</p>
                <button 
                  onClick={() => setShowAddForm(true)} 
                  className="mt-4 text-blue-400 hover:text-blue-300 hover:underline text-sm"
                >
                  Click here to add a model
                </button>
              </div>
            ) : (
              modalityOrder.map(modality => {
                const modalityIntegrations = groupedIntegrations[modality];
                if (!modalityIntegrations) return null;
                
                return (
                  <div key={modality} className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <h2 className="text-sm font-mono uppercase tracking-wider text-[#6b89c0]">
                        {modality.replace('_', ' ')} Models
                      </h2>
                      <span className="text-xs text-zinc-500">({modalityIntegrations.length})</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                      {modalityIntegrations.map((integration) => (
                        <ModelCard key={integration.id} integration={integration} />
                      ))}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ModelCard({ integration }: { integration: ModelIntegration }) {
  const gradientClass = getModalityGradient(integration.modality);
  
  return (
    <div className="group relative h-[160px] overflow-hidden cursor-pointer">
      {/* Gradient Background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-90`} />
      
      {/* Content */}
      <div className="relative h-full p-4 flex flex-col justify-between">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            {integration.source === 'github' ? (
              <Github size={18} className="text-white/80" />
            ) : (
              <Package size={18} className="text-white/80" />
            )}
            <div className="flex items-center space-x-2">
              {getStatusIcon(integration.status)}
            </div>
          </div>
        </div>

        {/* Model Info */}
        <div className="flex-1 flex flex-col justify-center">
          <h3 className="text-lg font-bold text-white mb-2 truncate" title={integration.name}>
            {integration.name}
          </h3>
          <p className="text-xs text-white/70 truncate mb-3" title={integration.url}>
            {integration.url}
          </p>
          
          {/* Tasks */}
          <div className="flex flex-wrap gap-1">
            {integration.tasks.slice(0, 2).map((task, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-white/20 rounded-full text-xs text-white/90 font-medium"
              >
                {task.replace('_', ' ')}
              </span>
            ))}
            {integration.tasks.length > 2 && (
              <span className="px-2 py-1 bg-white/20 rounded-full text-xs text-white/90 font-medium">
                +{integration.tasks.length - 2}
              </span>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-xs text-white/70">
          Started: {formatDate(integration.startedAt)}
        </div>
      </div>

      {/* Hover Overlay */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300" />
    </div>
  );
}

function AddModelForm({ onSubmit, onCancel }: { 
  onSubmit: (data: { source: 'github' | 'pip'; url: string }) => void;
  onCancel: () => void;
}) {
  const [source, setSource] = useState<'github' | 'pip'>('github');
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit({ source, url: url.trim() });
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="border-2 border-[#101827] bg-[#050a14] rounded-lg p-4">
        <h2 className="text-md font-semibold text-zinc-200 mb-4">Add New Model</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Source</label>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setSource('github')}
                className={`flex-1 py-2 px-3 rounded border transition-colors ${
                  source === 'github'
                    ? 'border-[#2a4170] bg-[#1a2438] text-white'
                    : 'border-[#1d2d50] bg-[#050a14] text-zinc-400 hover:border-[#2a4170]'
                }`}
              >
                GitHub
              </button>
              <button
                type="button"
                onClick={() => setSource('pip')}
                className={`flex-1 py-2 px-3 rounded border transition-colors ${
                  source === 'pip'
                    ? 'border-[#2a4170] bg-[#1a2438] text-white'
                    : 'border-[#1d2d50] bg-[#050a14] text-zinc-400 hover:border-[#2a4170]'
                }`}
              >
                PyPI
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              {source === 'github' ? 'Repository URL' : 'Package Name'}
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={source === 'github' ? 'https://github.com/user/repo' : 'package-name'}
              className="w-full px-3 py-2 bg-[#050a14] border border-[#1d2d50] rounded text-white focus:outline-none focus:border-[#2a4170]"
              required
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2 text-zinc-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!url.trim()}
              className="flex-1 py-2 bg-[#2a4170] hover:bg-[#1d2d50] disabled:bg-[#1d2d50] disabled:text-zinc-500 text-white rounded transition-colors"
            >
              Add Model
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 