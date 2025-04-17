'use client';

import { useState, useRef } from 'react';
import { Upload, X, Folder, Cloud, Database, Lock } from 'lucide-react';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { useJobs } from '@/hooks';
import { IntegrationSource } from '@/types/jobs';

interface IntegrationMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: () => void;
}

export default function IntegrationMenu({ isOpen, onClose, onAdd }: IntegrationMenuProps) {
  const [selectedSource, setSelectedSource] = useState<IntegrationSource>('directory');
  const [files, setFiles] = useState<FileList | null>(null);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data: session } = useSession();
  const { triggerJob } = useJobs();

  if (!session) {
    redirect("/login");
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(e.dataTransfer.files);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!files || files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    if (!description.trim()) {
      setError('Please provide a description');
      return;
    }
    
    setError(null);

    try {
      await triggerJob({
        files: Array.from(files),
        data_description: description,
        data_source: selectedSource,
        type: "integration"
      });
      onClose();
      onAdd();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    }
  };

  if (!isOpen) return null;

  const sourceOptions = [
    { id: 'directory', label: 'Directory', icon: Folder, available: true },
    { id: 'aws', label: 'AWS S3', icon: Cloud, available: false },
    { id: 'azure', label: 'Azure Blob', icon: Database, available: false },
    { id: 'gcp', label: 'Google Cloud', icon: Lock, available: false },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-2xl p-6 bg-zinc-900 rounded-lg shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-medium text-white">Integrate New Dataset</h2>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-zinc-800 transition-colors"
          >
            <X size={18} className="text-zinc-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Source Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-zinc-400 mb-3">
              Select Data Source
            </label>
            <div className="grid grid-cols-4 gap-3">
              {sourceOptions.map((source) => {
                const Icon = source.icon;
                return (
                  <button
                    key={source.id}
                    type="button"
                    onClick={() => source.available && setSelectedSource(source.id as IntegrationSource)}
                    className={`p-4 rounded-lg border-2 transition-all duration-200 flex flex-col items-center gap-2
                      ${selectedSource === source.id 
                        ? 'border-blue-500 bg-blue-900/10' 
                        : source.available 
                          ? 'border-zinc-700 hover:border-zinc-500' 
                          : 'border-zinc-800 bg-zinc-800/50 cursor-not-allowed opacity-50'
                      }`}
                    disabled={!source.available}
                  >
                    <Icon size={20} className={selectedSource === source.id ? 'text-blue-400' : 'text-zinc-400'} />
                    <span className="text-sm font-medium text-white">{source.label}</span>
                    {!source.available && (
                      <span className="text-xs text-zinc-500">Coming Soon</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* File Upload Area */}
          {selectedSource === 'directory' && (
            <div className="mb-6">
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                  ${files ? 'border-blue-500 bg-blue-900/10' : 'border-zinc-700 hover:border-zinc-500'}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <input 
                  type="file" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  multiple
                  className="hidden" 
                />
                
                {files ? (
                  <div className="flex flex-col items-center">
                    <Upload size={24} className="text-blue-400 mb-2" />
                    <p className="text-sm font-medium text-white">{files.length} file{files.length !== 1 ? 's' : ''} selected</p>
                    <p className="text-xs text-zinc-400">
                      {Array.from(files).reduce((acc, file) => acc + file.size, 0) / 1024 / 1024 > 1
                        ? `${(Array.from(files).reduce((acc, file) => acc + file.size, 0) / 1024 / 1024).toFixed(1)} MB`
                        : `${(Array.from(files).reduce((acc, file) => acc + file.size, 0) / 1024).toFixed(1)} KB`}
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <Upload size={24} className="text-zinc-500 mb-2" />
                    <p className="text-sm font-medium text-white">Drag & drop files here</p>
                    <p className="text-xs text-zinc-500">Or click to browse</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Description Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-zinc-400 mb-1">
              Dataset Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this dataset contains..."
              className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-md text-white text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              rows={4}
            />
          </div>

          {error && (
            <div className="mb-6 p-3 bg-red-900/20 border border-red-800 rounded-md text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-md hover:bg-zinc-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 transition-colors disabled:opacity-50 flex items-center"
            >
              Start Integration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 