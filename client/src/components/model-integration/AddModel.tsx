'use client';

import React, { useState, useEffect } from 'react';
import { Check, AlertTriangle, Loader2, Github, Package, Brain, Zap } from 'lucide-react';

interface AddModelProps {
  setCurrentView: (view: 'overview' | 'add' | 'jobs') => void;
}

type ModelSource = 'github' | 'pip';

export default function AddModel({ setCurrentView }: AddModelProps) {
  const [modelSource, setModelSource] = useState<ModelSource>('github');
  const [url, setUrl] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const resetForm = () => {
    setUrl('');
    setUploadError(null);
    setModelSource('github');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setUploadError(modelSource === 'github' ? 'Please provide a GitHub repository URL' : 'Please provide a package name');
      return;
    }

    setUploadError(null);
    setIsUploading(true);

    try {
      // Mock API call - replace with actual integration
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock success
      resetForm();
      setCurrentView('overview');
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "An unknown error occurred during integration");
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    resetForm();
  }, []);

  return (
    <>
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0">
        <h3 className="text-md font-semibold text-zinc-200">Integrate New Model</h3>
      </div>
      <div className="flex-grow p-6 overflow-y-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
           <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Select Model Source
                </label>
                <div className="grid grid-cols-2 gap-3">
                   <button
                       type="button"
                       onClick={() => setModelSource('github')}
                       className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 ${
                           modelSource === 'github'
                           ? 'border-blue-600 bg-blue-900/20 text-blue-300 shadow-md'
                           : 'border-zinc-700 bg-[#0a101c]/50 text-zinc-400 hover:border-zinc-600 hover:bg-[#0a101c]'
                       }`}
                   >
                       <Github size={24} className="mb-2" />
                       <span className="text-xs font-medium">GitHub Repository</span>
                   </button>
                    <button
                       type="button"
                       onClick={() => setModelSource('pip')}
                       className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 ${
                           modelSource === 'pip'
                           ? 'border-orange-600 bg-orange-900/20 text-orange-300 shadow-md'
                           : 'border-zinc-700 bg-[#0a101c]/50 text-zinc-400 hover:border-zinc-600 hover:bg-[#0a101c]'
                       }`}
                   >
                       <Package size={24} className="mb-2" />
                       <span className="text-xs font-medium">PyPI Package</span>
                   </button>
                </div>
           </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1.5">
              {modelSource === 'github' ? 'Repository URL' : 'Package Name'}
            </label>
            <div className="relative">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={modelSource === 'github' ? 'https://github.com/user/repo' : 'package-name'}
                className="w-full px-3 py-2 bg-[#0a101c] border border-zinc-700 rounded-md text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                required
              />
              {url && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <Check size={16} className="text-green-400" />
                </div>
              )}
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              {modelSource === 'github' 
                ? 'Provide the full GitHub repository URL' 
                : 'Enter the PyPI package name (e.g., "tensorflow", "scikit-learn")'
              }
            </p>
          </div>

          <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
            <div className="flex items-start space-x-3">
              <Brain size={20} className="text-blue-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-blue-300 mb-1">AI-Powered Integration</h4>
                <p className="text-xs text-blue-200 leading-relaxed">
                  Our AI will automatically analyze the model, detect its architecture, 
                  and set up the appropriate integration pipeline. You can review and 
                  approve each step of the process.
                </p>
              </div>
            </div>
          </div>

          {uploadError && (
           <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-md text-sm text-red-300 flex items-center">
               <AlertTriangle size={16} className="mr-2 flex-shrink-0"/>
              {uploadError}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isUploading || !url.trim()}
              className="px-5 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-md hover:from-blue-500 hover:to-blue-600 transition-all shadow-md hover:shadow-lg border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:from-zinc-600 disabled:to-zinc-700 disabled:border-zinc-500 flex items-center"
            >
              {isUploading ? (
                 <>
                   <Loader2 size={16} className="animate-spin mr-2" /> Integrating...
                 </>
              ) : (
                 <>
                   <Zap size={16} className="mr-1.5" /> Integrate Model
                 </>
              )}
            </button>
          </div>
        </form>
      </div>
    </>
  );
} 