'use client';

import { useState, useRef } from 'react';
import { Upload, X, Loader2 } from 'lucide-react';

interface AddDatasetProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: () => void;
}

export default function AddDataset({ isOpen, onClose, onAdd }: AddDatasetProps) {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "text/csv") {
        setError("Only CSV files are supported");
        return;
      }
      setFile(selectedFile);
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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type !== "text/csv") {
        setError("Only CSV files are supported");
        return;
      }
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    if (!description.trim()) {
      setError('Please provide a description');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('data_description', description);

      const response = await fetch(`/api/proxy/data/call-integration-agent`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload dataset');
      }

      onClose();
      onAdd();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-md p-6 bg-zinc-900 rounded-lg shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-white">Add New Dataset</h2>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-zinc-800 transition-colors"
          >
            <X size={18} className="text-zinc-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <div 
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
                ${file ? 'border-blue-500 bg-blue-900/10' : 'border-zinc-700 hover:border-zinc-500'}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".csv"
                className="hidden" 
              />
              
              {file ? (
                <div className="flex flex-col items-center">
                  <Upload size={24} className="text-blue-400 mb-2" />
                  <p className="text-sm font-medium text-white">{file.name}</p>
                  <p className="text-xs text-zinc-400">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <Upload size={24} className="text-zinc-500 mb-2" />
                  <p className="text-sm font-medium text-white">Drag & drop a CSV file here</p>
                  <p className="text-xs text-zinc-500">Or click to browse</p>
                </div>
              )}
            </div>
          </div>

          <div className="mb-4">
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
            <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded-md text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-md hover:bg-zinc-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 transition-colors disabled:opacity-50 flex items-center"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={16} className="mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Upload Dataset'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
