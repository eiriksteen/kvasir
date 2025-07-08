'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Plus, Upload, Check, AlertTriangle, Loader2, HardDrive, Cloud, X } from 'lucide-react';
import { useJobs } from '@/hooks';
import { useSession } from 'next-auth/react';
import { IntegrationSource } from '@/types/jobs';

interface AddDatasetModalProps {
  onClose: () => void;
  gradientClass?: string;
}

export default function AddDatasetModal({ onClose, gradientClass }: AddDatasetModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [dataSource, setDataSource] = useState<IntegrationSource>('local');
  const [description, setDescription] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { triggerJob } = useJobs('integration');
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
        const selectedFiles = Array.from(e.target.files);

        if (selectedFiles.length === 0) {
            setUploadError("No files selected or directory is empty.");
            setFiles([]);
            return;
        }

      setFiles(selectedFiles);
      setUploadError(null);
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
      const droppedFiles = Array.from(e.dataTransfer.files);
      setFiles(droppedFiles);
      setUploadError(null);
    }
  };

  const resetForm = () => {
    setFiles([]); 
    setDescription('');
    setUploadError(null);
    setDataSource('local');
    if(fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (files.length === 0) {
      setUploadError(dataSource === 'local' ? 'Please select a directory containing CSV files' : 'Please select files');
      return;
    }

    if (!description.trim()) {
      setUploadError('Please provide a description');
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
        files: files, 
        dataDescription: description,
        dataSource: dataSource, 
        type: "integration"
      });
      resetForm(); 
      onClose(); // Close modal after successful submission
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "An unknown error occurred during upload");
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
            <h3 className="text-xl font-semibold text-zinc-200">Integrate New Dataset</h3>
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
                      Select Data Source
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                       <button
                           type="button"
                           onClick={() => setDataSource('local')}
                           className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 ${
                               dataSource === 'local'
                               ? 'border-blue-600 bg-blue-900/20 text-blue-300 shadow-md'
                               : 'border-zinc-700 bg-[#0a101c]/50 text-zinc-400 hover:border-zinc-600 hover:bg-[#0a101c]'
                           }`}
                       >
                           <HardDrive size={24} className="mb-2" />
                           <span className="text-xs font-medium">Local</span>
                       </button>
                        <button
                           type="button"
                           disabled
                           onClick={() => setDataSource('aws')}
                           className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 relative overflow-hidden ${
                               dataSource === 'aws'
                               ? 'border-orange-600 bg-orange-900/20 text-orange-300 shadow-md'
                               : 'border-zinc-800 bg-[#050a14]/30 text-zinc-600 cursor-not-allowed'
                           }`}
                           title="AWS S3 integration coming soon"
                       >
                           <Cloud size={24} className="mb-2" />
                           <span className="text-xs font-medium">AWS S3</span>
                           <span className="absolute bottom-1 right-1 text-[10px] bg-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">Soon</span>
                       </button>
                        <button
                           type="button"
                           disabled
                           onClick={() => setDataSource('gcp')}
                           className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 relative overflow-hidden ${
                               dataSource === 'gcp'
                               ? 'border-sky-600 bg-sky-900/20 text-sky-300 shadow-md'
                               : 'border-zinc-800 bg-[#050a14]/30 text-zinc-600 cursor-not-allowed'
                           }`}
                           title="Google Cloud Storage integration coming soon"
                       >
                           <Cloud size={24} className="mb-2" />
                           <span className="text-xs font-medium">Google Cloud</span>
                           <span className="absolute bottom-1 right-1 text-[10px] bg-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">Soon</span>
                       </button>
                        <button
                           type="button"
                           disabled
                           onClick={() => setDataSource('azure')}
                           className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 text-center transition-colors duration-150 h-24 relative overflow-hidden ${
                               dataSource === 'azure'
                               ? 'border-indigo-600 bg-indigo-900/20 text-indigo-300 shadow-md'
                               : 'border-zinc-800 bg-[#050a14]/30 text-zinc-600 cursor-not-allowed'
                           }`}
                           title="Azure Blob Storage integration coming soon"
                       >
                           <Cloud size={24} className="mb-2" />
                           <span className="text-xs font-medium">Azure Storage</span>
                           <span className="absolute bottom-1 right-1 text-[10px] bg-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">Soon</span>
                       </button>
                    </div>
               </div>

              {dataSource === 'local' && (
                <div>
                   <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                   Upload Directory
                   </label>
                   <div
                      className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors duration-200 min-h-[160px] flex items-center justify-center
                        ${files.length > 0 ? 'border-blue-700/50 bg-blue-900/10' : 'border-zinc-700 hover:border-zinc-600 bg-[#0a101c]/30 hover:bg-[#0a101c]/60'}`}
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                   >
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        className="hidden"
                        {...({ webkitdirectory: "true", mozdirectory: "true", directory: "true", multiple: true })}
                      />

                      {files.length > 0 ? (
                        <div className="flex flex-col items-center text-zinc-200">
                          <Check size={28} className="text-green-400 mb-2" />
                          <p className="text-sm font-medium">
                              {files.length} file{files.length > 1 ? 's' : ''} selected
                           </p>
                           <p className="text-xs text-zinc-400 mt-1">
                               Total size: {(files.reduce((acc, file) => acc + file.size, 0) / 1024).toFixed(1)} KB
                           </p>
                           <button
                               type="button"
                               onClick={(e) => { e.stopPropagation(); resetForm(); }}
                               className="mt-3 text-xs text-red-400 hover:underline"
                           >
                               Clear selection
                           </button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center text-zinc-400">
                          <Upload size={28} className="text-zinc-500 mb-3" />
                          <p className="text-sm font-medium text-zinc-300">Drag & drop a directory here</p>
                          <p className="text-xs text-zinc-500 mt-1">Or click to browse and select a folder</p>
                        </div>
                      )}
                   </div>
                </div>
              )}

              {(dataSource === 'aws' || dataSource === 'gcp' || dataSource === 'azure') && (
                   <div className="p-4 bg-zinc-800/50 border border-zinc-700 rounded-md text-center text-zinc-400">
                      <p className="font-medium">Configuration for {dataSource.toUpperCase()} is coming soon.</p>
                      <p className="text-xs mt-1">Please select &apos;Local&apos; for now.</p>
                  </div>
              )}

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Dataset Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the columns, content, and purpose of this data..."
                  className="w-full px-3 py-2 bg-[#0a101c] border border-zinc-700 rounded-md text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                  rows={4}
                  required
                />
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
                  disabled={isUploading || dataSource !== 'local' || files.length === 0 || !description.trim()}
                  className="px-5 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-md hover:from-blue-500 hover:to-blue-600 transition-all shadow-md hover:shadow-lg border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:from-zinc-600 disabled:to-zinc-700 disabled:border-zinc-500 flex items-center"
                >
                  {isUploading ? (
                     <>
                       <Loader2 size={16} className="animate-spin mr-2" /> Processing...
                     </>
                  ) : (
                     <>
                       <Plus size={16} className="mr-1.5" /> Integrate Dataset
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
