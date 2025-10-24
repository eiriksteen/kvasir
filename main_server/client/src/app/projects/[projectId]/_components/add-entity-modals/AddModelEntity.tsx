'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Github, Package } from 'lucide-react';
import { UUID } from 'crypto';
import { useProjectChat } from '@/hooks';

type ModelSourceType = "github" | "pypi";

interface ModelSourceFields {
  repoUrl?: string;
  packageName?: string;
  packageVersion?: string;
  modelName?: string;
}

interface AddModelEntityProps {
  onClose: () => void;
  projectId: UUID;
}

const MODEL_SOURCES: ModelSourceType[] = ["github", "pypi"];

const getSourceIcon = (source: ModelSourceType) => {
  switch (source) {
    case 'github': return <Github size={16} />;
    case 'pypi': return <Package size={16} />;
  }
};

const getSourceLabel = (source: ModelSourceType) => {
  switch (source) {
    case 'github': return 'GitHub Repository';
    case 'pypi': return 'PyPI Package';
  }
};

export default function AddModelEntity({ onClose, projectId }: AddModelEntityProps) {
  const [selectedSource, setSelectedSource] = useState<ModelSourceType | null>(null);
  const [description, setDescription] = useState('');
  const [fields, setFields] = useState<ModelSourceFields>({});
  const { submitPrompt } = useProjectChat(projectId);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (backdropRef.current && event.target === backdropRef.current) {
        onClose();
      }
    };

    const backdrop = backdropRef.current;
    if (backdrop) {
      backdrop.addEventListener('click', handleClickOutside);
      return () => backdrop.removeEventListener('click', handleClickOutside);
    }
  }, [onClose]);

  const handleSourceSelect = (source: ModelSourceType) => {
    setSelectedSource(source);
    setFields({}); // Reset fields when source changes
  };

  const handleFieldChange = (field: keyof ModelSourceFields, value: string) => {
    setFields(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!selectedSource) return;

    let prompt = `Create a new model entity from ${getSourceLabel(selectedSource).toLowerCase()} source:`;

    switch (selectedSource) {
      case 'github':
        if (fields.repoUrl) prompt += `\nRepository URL: ${fields.repoUrl}`;
        break;
      case 'pypi':
        if (fields.packageName) prompt += `\nPackage name: ${fields.packageName}`;
        if (fields.packageVersion) prompt += `\nVersion: ${fields.packageVersion}`;
        break;
    }

    if (description.trim()) {
      prompt += `\n\nDescription: ${description}`;
    }

    await submitPrompt(prompt);
    onClose();
  };

  const renderSourceFields = () => {
    if (!selectedSource) return null;

    switch (selectedSource) {
      case 'github':
        return (
          <div className="mb-4">
            <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-900 mb-2">
              Repository URL
            </label>
            <input
              id="repoUrl"
              type="url"
              value={fields.repoUrl || ''}
              onChange={(e) => handleFieldChange('repoUrl', e.target.value)}
              placeholder={`https://github.com/username/repo`}
              className="w-full p-2 bg-gray-50 border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#000034]/50 focus:border-[#000034]/50 transition-all duration-200 text-sm"
            />
          </div>
        );

      case 'pypi':
        return (
          <>
            <div className="mb-4">
              <label htmlFor="packageName" className="block text-sm font-medium text-gray-900 mb-2">
                Package Name
              </label>
              <input
                id="packageName"
                type="text"
                value={fields.packageName || ''}
                onChange={(e) => handleFieldChange('packageName', e.target.value)}
                placeholder="e.g., torch, transformers, sklearn"
                className="w-full p-2 bg-gray-50 border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#000034]/50 focus:border-[#000034]/50 transition-all duration-200 text-sm"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="packageVersion" className="block text-sm font-medium text-gray-900 mb-2">
                Version <span className="text-xs text-gray-500">(optional)</span>
              </label>
              <input
                id="packageVersion"
                type="text"
                value={fields.packageVersion || ''}
                onChange={(e) => handleFieldChange('packageVersion', e.target.value)}
                placeholder="e.g., 2.0.1, latest"
                className="w-full p-2 bg-gray-50 border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#000034]/50 focus:border-[#000034]/50 transition-all duration-200 text-sm"
              />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  function submitIsDisabled() {
    if (!selectedSource) return true;
    if (selectedSource === 'github') {
      return !fields.repoUrl;
    }
    if (selectedSource === 'pypi') {
      return !fields.packageName;
    } 
    return false;
  }

  return (
    <div ref={backdropRef} className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-[#491A32]/20 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600 mb-6">Add Model</h3>

          {/* Model Source Selection */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Select Model Source</h4>
            <div className="grid grid-cols-2 gap-2">
              {MODEL_SOURCES.map((source) => (
                <button
                  key={source}
                  onClick={() => handleSourceSelect(source)}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 ${
                    selectedSource === source
                      ? 'bg-gray-50 border-[#000034]/50 text-[#000034]'
                      : 'bg-gray-50 border-gray-300 hover:bg-gray-100 hover:border-gray-400 text-gray-600'
                  }`}
                >
                  <div className={`p-1 rounded ${
                    selectedSource === source ? 'bg-[#000034]/20' : 'bg-gray-200'
                  }`}>
                    {getSourceIcon(source)}
                  </div>
                  <span className="text-sm font-medium">{getSourceLabel(source)}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Source Fields */}
          {selectedSource && (
            <div className="mb-6">
              {renderSourceFields()}
            </div>
          )}

          {/* Model Description */}
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-900 mb-2">
              Description <span className="text-xs text-gray-500">(optional)</span>
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optionally describe the model."
              className="w-full h-24 p-2 bg-gray-50 border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#000034]/50 focus:border-[#000034]/50 transition-all duration-200 resize-none text-sm"
            />
          </div>

          {/* Submit Button */}
          <div className="mt-auto border-t border-gray-200 pt-4">
            <button
              onClick={handleSubmit}
              disabled={submitIsDisabled()}
              className="w-full h-10 flex items-center justify-center gap-2 px-4 bg-[#000034] hover:bg-[#000044] disabled:bg-gray-300 disabled:text-gray-500 text-white font-medium rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
            >
              <Package size={16} />
              Create Model
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 