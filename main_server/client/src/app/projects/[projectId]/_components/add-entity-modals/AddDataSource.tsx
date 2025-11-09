'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Upload, Check, AlertTriangle, Loader2 } from 'lucide-react';
import { useDataSources } from '@/hooks/useDataSources';
import { useSession } from "next-auth/react";
import { UUID } from 'crypto';

interface AddDataSourceProps {
  onClose: () => void;
  projectId: UUID;
}

export default function AddDataSource({ onClose, projectId }: AddDataSourceProps) {
  const { triggerCreateFileDataSource, mutateDataSources } = useDataSources(projectId);
  const { data: session } = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

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

  // Handle click outside to close
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

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

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
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (files.length === 0) {
      setUploadError('Please select at least one file to upload');
      return;
    }

    if (!session) {
      setUploadError('Session expired. Please log in again.');
      return;
    }

    setUploadError(null);
    setIsUploading(true);

    try {
      await triggerCreateFileDataSource({
        files: files,
      });
      resetForm();
      await mutateDataSources();
      onClose();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "An unknown error occurred during upload");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div ref={backdropRef} className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-gray-300 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600">Add Data Source</h3>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col flex-grow overflow-hidden">
            <div className="flex-grow overflow-y-auto p-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Upload File
                </label>
                <div
                  className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors duration-200 min-h-[160px] flex items-center justify-center
                    ${files.length > 0 ? 'border-[#000034]/50 bg-[#000034]/10' : 'border-gray-300 hover:border-[#000034] bg-gray-50 hover:bg-gray-100'}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    multiple
                  />

                  {files.length > 0 ? (
                    <div className="flex flex-col items-center text-gray-800">
                      <Check size={28} className="text-green-600 mb-2" />
                      <p className="text-sm font-medium">
                        {files.length} file{files.length > 1 ? 's' : ''} selected
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {files.length === 1 ? files[0].name : `${files[0].name} and ${files.length - 1} more`}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        Total size: {(files.reduce((acc, file) => acc + file.size, 0) / 1024).toFixed(1)} KB
                      </p>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); resetForm(); }}
                        className="mt-3 text-xs text-red-600 hover:underline"
                      >
                        Clear selection
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center text-gray-600">
                      <Upload size={28} className="text-gray-400 mb-3" />
                      <p className="text-sm font-medium text-gray-700">Drag & drop files here</p>
                      <p className="text-xs text-gray-500 mt-1">Or click to browse and select files (multiple files supported)</p>
                    </div>
                  )}
                </div>
              </div>

              {uploadError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800 flex items-center">
                  <AlertTriangle size={16} className="mr-2 flex-shrink-0"/>
                  {uploadError}
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 bg-gray-100 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-200 hover:border-gray-400 transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isUploading || files.length === 0}
                className="px-5 py-2 bg-[#000034] text-white rounded-md hover:bg-[#000028] transition-all shadow-md hover:shadow-lg border border-[#000034] disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:bg-gray-400 disabled:border-gray-400 flex items-center"
              >
                {isUploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin mr-2" /> Processing...
                  </>
                ) : (
                  <>
                    <Upload size={16} className="mr-1.5" />Add Data Source
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}