import { X, BarChart3, FileText as FileDescription, Shield } from 'lucide-react';
import { useEffect } from 'react';
import { useDataSource } from "@/hooks/useDataSources";
import { UUID } from 'crypto';
import { TabularFileDataSource, DataSource } from "@/types/data-sources";

interface FileInfoModalProps {
  dataSourceId: UUID;
  onClose: () => void;
}

export default function FileInfoModal({ 
  dataSourceId, 
  onClose
}: FileInfoModalProps) {
  
  const { dataSource } = useDataSource(dataSourceId);

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
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [onClose]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!dataSource) {
    return null;
  }

  // Type guard to check if we have full tabular data
  const isTabularFileDataSource = (source: DataSource): source is TabularFileDataSource => {
    return 'numRows' in source;
  };

  const hasFullData = isTabularFileDataSource(dataSource);
  const hasAnalysis = hasFullData && dataSource.analysis;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={() => onClose()}
      />
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden bg-black/50 rounded-lg">
          <div className="rounded-xl border-2 border-gray-500/20 shadow-xl shadow-gray-500/10 h-full flex flex-col">
            <div className="relative flex items-center p-4 border-b border-gray-500/20 flex-shrink-0">
              <div className="ml-2">
                <h3 className="text-sm font-mono tracking-wider text-gray-200">
                  {dataSource.name}
                </h3>
              </div>
              <button
                onClick={() => onClose()}
                className="absolute right-6 text-gray-400 hover:text-white transition-colors"
                title="Close modal"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 flex-1 overflow-y-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {/* Left Column - File Stats and Content Description */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-gray-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-gray-500/20 rounded-lg">
                        <BarChart3 size={18} className="text-gray-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-200">
                          {hasFullData ? 'File Stats' : 'Data Source Info'}
                        </h3>
                        <p className="text-xs text-gray-400 font-mono">{dataSource.type}</p>
                      </div>
                    </div>
                    <div className="space-y-2 flex-1 overflow-y-auto pr-2 min-h-0">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-300/80">Created:</span>
                        <span className="text-sm text-gray-200 font-mono ml-2">{formatDate(dataSource.createdAt)}</span>
                      </div>
                      
                      {hasFullData && (
                        <>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-300/80">File Name:</span>
                            <span className="text-sm text-gray-200 font-mono">{dataSource.fileName}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-300/80">File Type:</span>
                            <span className="text-sm text-gray-200 font-mono">{dataSource.fileType}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-300/80">Rows:</span>
                            <span className="text-sm text-gray-200 font-mono">{dataSource.numRows.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-300/80">Columns:</span>
                            <span className="text-sm text-gray-200 font-mono">{dataSource.numColumns.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-300/80">File Size:</span>
                            <span className="text-sm text-gray-200 font-mono">
                              {(dataSource.fileSizeBytes / (1024 * 1024)).toFixed(2)} MB
                            </span>
                          </div>
                        </>
                      )}
                      
                    </div>
                  </div>

                  <div className={`border border-blue-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                    hasAnalysis && dataSource.analysis.contentDescription
                      ? 'bg-gradient-to-br from-zinc-900/80 to-zinc-800/40'
                      : 'bg-black/60'
                  }`}>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-blue-500/20 rounded-lg">
                        <FileDescription size={18} className="text-blue-300" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Content Description</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      { hasAnalysis && dataSource.analysis.contentDescription ?
                        <p className="text-sm text-gray-300/80 leading-relaxed">{dataSource.analysis.contentDescription}</p>
                        :
                        <div className="flex items-center justify-center h-full">
                          <p className="text-sm text-gray-400/80 leading-relaxed text-center font-medium">Working on it...</p>
                        </div>
                      }
                    </div>
                  </div>


                </div>

                {/* Right Column - More Analysis Information */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                    <>

                        <div className={`border border-orange-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                          hasAnalysis && dataSource.analysis.qualityDescription
                            ? 'bg-gradient-to-br from-zinc-900/80 to-zinc-800/40'
                            : 'bg-black/60'
                        }`}>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <div className="p-2 bg-orange-500/20 rounded-lg">
                              <Shield size={18} className="text-orange-300" />
                            </div>
                            <h3 className="text-sm font-semibold text-gray-200">Quality Assessment</h3>
                          </div>
                          <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                            { hasAnalysis && dataSource.analysis.qualityDescription ?
                              <p className="text-sm text-gray-300/80 leading-relaxed">{dataSource.analysis.qualityDescription}</p>
                              :
                              <div className="flex items-center justify-center h-full">
                                <p className="text-sm text-gray-400/80 leading-relaxed text-center font-medium">Working on it...</p>
                              </div>
                            }
                          </div>
                        </div>


                        <div className={`border border-red-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                          hasAnalysis && dataSource.analysis.cautions
                            ? 'bg-gradient-to-br from-zinc-900/80 to-zinc-800/40'
                            : 'bg-black/60'
                        }`}>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <div className="p-2 bg-red-500/20 rounded-lg">
                              <Shield size={18} className="text-red-300" />
                            </div>
                            <h3 className="text-sm font-semibold text-gray-200">Cautions</h3>
                          </div>
                          <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                            {hasAnalysis && dataSource.analysis.cautions ?
                              <p className="text-sm text-gray-300/80 leading-relaxed">{dataSource.analysis.cautions}</p>
                              :
                              <div className="flex items-center justify-center h-full">
                                <p className="text-sm text-gray-400/80 leading-relaxed text-center font-medium">Working on it...</p>
                              </div>
                            }
                          </div>
                        </div>
                    </>

                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}