import { useDataSources } from "@/hooks/useDataSources";
import { useSession } from "next-auth/react";
import { useState, useRef, useEffect } from 'react';
import { Plus, X, Upload, Check, AlertTriangle, Loader2 } from 'lucide-react';
import { SupportedSource } from "@/types/data-integration";
import SourceTypeIcon from "./SourceTypeIcon";

// Add Data Source Modal
export default function AddDataSourceModal({ 
  isOpen, 
  onClose, 
  selectedSourceType 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  selectedSourceType: SupportedSource | null; 
  setSelectedSourceType: (sourceType: SupportedSource | null) => void; 
}) {
  const { triggerCreateFileDataSource } = useDataSources();
  const { data: session } = useSession();
  const [files, setFiles] = useState<File[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

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
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (files.length === 0) {
      setUploadError('Please select a directory containing files');
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
      onClose();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "An unknown error occurred during upload");
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      resetForm();
    }
  }, [isOpen]);

  if (!isOpen || !selectedSourceType) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="relative bg-[#050a14] rounded-xl border-2 border-[#101827] w-full max-w-6xl h-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative flex items-center p-6 border-b border-[#101827] flex-shrink-0">
              {/* Add icon here */}
              <SourceTypeIcon type={selectedSourceType} size={16} />
              <h3 className="text-base font-mono uppercase tracking-wider text-gray-400 flex-grow pl-3">
                Add {selectedSourceType}
              </h3>
              <button
                onClick={onClose}
                className="text-zinc-400 hover:text-zinc-300 transition-colors"
                title="Close modal"
              >
                <X size={20} />
              </button>
            </div>
    
            <div className="space-y-6 relative flex-grow p-6 overflow-y-auto">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Upload Files
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
                  disabled={isUploading || files.length === 0}
                  className="px-5 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-md hover:from-blue-500 hover:to-blue-600 transition-all shadow-md hover:shadow-lg border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:from-zinc-600 disabled:to-zinc-700 disabled:border-zinc-500 flex items-center"
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={16} className="animate-spin mr-2" /> Processing...
                    </>
                  ) : (
                    <>
                      <Plus size={16} className="mr-1.5" />Add Data Source
                    </>
                  )}
                </button>
              </div>
            </div>

            {uploadError && (
              <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-md text-sm text-red-300 flex items-center">
                <AlertTriangle size={16} className="mr-2 flex-shrink-0"/>
                {uploadError}
              </div>
            )}
          </form>
        </div>
      </div>
    </>
  );
}