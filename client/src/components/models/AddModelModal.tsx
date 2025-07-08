'use client';

import React, { useState, useEffect } from 'react';
import { Check, AlertTriangle, Loader2, Github, Package, Brain, Zap, X } from 'lucide-react';
import { useJobs } from '@/hooks';
import { useSession } from 'next-auth/react';

interface AddModelModalProps {
  onClose: () => void;
  gradientClass?: string;
}

type ModelSource = 'github' | 'pip';

export default function AddModelModal({ onClose, gradientClass }: AddModelModalProps) {
  const [modelSource, setModelSource] = useState<ModelSource>('github');
  const [url, setUrl] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const { triggerJob } = useJobs('model_integration');
  const { data: session } = useSession();

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

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

    if (!session) {
      setUploadError('Session expired. Please log in again.');
      return;
    }

    setUploadError(null);
    setIsUploading(true);

    try {
      await triggerJob({
        modelId: url,
        source: modelSource,
        type: 'model_integration'
      });
      
      resetForm();
      onClose(); // Close modal after successful submission
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
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="relative bg-[#050a14] rounded-xl border-2 border-[#101827] w-full max-w-4xl h-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          {gradientClass && (
            <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-xl pointer-events-none`} />
          )}
          
          <div className="relative flex items-center justify-between p-6 border-b border-[#101827] flex-shrink-0">
            <h3 className="text-xl font-semibold text-zinc-200">Integrate New Model</h3>
            <button
              onClick={onClose}
              className="text-zinc-400 hover:text-zinc-300 transition-colors"
              title="Close modal"
            >
              <X size={20} />
            </button>
          </div>
          
          <div className="relative flex-grow p-6 overflow-y-auto">
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

              <div className="flex justify-end pt-2 gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2 bg-zinc-800/50 border border-zinc-700 text-zinc-300 rounded-md hover:bg-zinc-700/50 hover:border-zinc-600 transition-all"
                >
                  Cancel
                </button>
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
        </div>
      </div>
    </>
  );
}
