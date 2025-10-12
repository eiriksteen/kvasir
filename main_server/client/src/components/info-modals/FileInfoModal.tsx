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
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full p-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {/* Left Column - File Stats and Content Description */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-gray-500/20 rounded-lg">
                        <BarChart3 size={18} className="text-gray-600" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900">
                          {hasFullData ? 'File Stats' : 'Data Source Info'}
                        </h3>
                        <p className="text-xs text-gray-600 font-mono">{dataSource.type}</p>
                      </div>
                    </div>
                    <div className="space-y-2 flex-1 overflow-y-auto pr-2 min-h-0">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600">Created:</span>
                        <span className="text-sm text-gray-900 font-mono ml-2">{formatDate(dataSource.createdAt)}</span>
                      </div>
                      
                      {hasFullData && (
                        <>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">File Name:</span>
                            <span className="text-sm text-gray-900 font-mono">{dataSource.fileName}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">File Type:</span>
                            <span className="text-sm text-gray-900 font-mono">{dataSource.fileType}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Rows:</span>
                            <span className="text-sm text-gray-900 font-mono">{dataSource.numRows.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Columns:</span>
                            <span className="text-sm text-gray-900 font-mono">{dataSource.numColumns.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">File Size:</span>
                            <span className="text-sm text-gray-900 font-mono">
                              {(dataSource.fileSizeBytes / (1024 * 1024)).toFixed(2)} MB
                            </span>
                          </div>
                        </>
                      )}
                      
                    </div>
                  </div>

                  <div className={`border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                    hasAnalysis && dataSource.analysis.contentDescription
                      ? 'bg-gradient-to-br from-gray-50 to-white'
                      : 'bg-gray-100'
                  }`}>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-gray-500/20 rounded-lg">
                        <FileDescription size={18} className="text-gray-600" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Content Description</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      { hasAnalysis && dataSource.analysis.contentDescription ?
                        <p className="text-sm text-gray-600 leading-relaxed">{dataSource.analysis.contentDescription}</p>
                        :
                        <div className="flex items-center justify-center h-full">
                          <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Working on it...</p>
                        </div>
                      }
                    </div>
                  </div>
                </div>

                {/* Right Column - More Analysis Information */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className={`border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                    hasAnalysis && dataSource.analysis.qualityDescription
                      ? 'bg-gradient-to-br from-gray-50 to-white'
                      : 'bg-gray-100'
                  }`}>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-gray-500/20 rounded-lg">
                        <Shield size={18} className="text-gray-600" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Quality Assessment</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      { hasAnalysis && dataSource.analysis.qualityDescription ?
                        <p className="text-sm text-gray-600 leading-relaxed">{dataSource.analysis.qualityDescription}</p>
                        :
                        <div className="flex items-center justify-center h-full">
                          <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Working on it...</p>
                        </div>
                      }
                    </div>
                  </div>

                  <div className={`border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0 ${
                    hasAnalysis && dataSource.analysis.cautions
                      ? 'bg-gradient-to-br from-gray-50 to-white'
                      : 'bg-gray-100'
                  }`}>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-gray-500/20 rounded-lg">
                        <Shield size={18} className="text-gray-600" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Cautions</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      {hasAnalysis && dataSource.analysis.cautions ?
                        <p className="text-sm text-gray-600 leading-relaxed">{dataSource.analysis.cautions}</p>
                        :
                        <div className="flex items-center justify-center h-full">
                          <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Working on it...</p>
                        </div>
                      }
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}