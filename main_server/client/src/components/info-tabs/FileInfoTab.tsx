import { BarChart3, Shield, X } from 'lucide-react';
import { useEffect } from 'react';
import { useDataSource } from "@/hooks/useDataSources";
import { UUID } from 'crypto';
import { TabularFileDataSourceInDB } from "@/types/data-sources";

interface FileInfoTabProps {
  dataSourceId: UUID;
  onClose: () => void;
  asModal?: boolean;
}

export default function FileInfoTab({ 
  dataSourceId, 
  onClose,
  asModal = false
}: FileInfoTabProps) {
  
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

  // Check if we have type-specific fields (e.g., tabular file data)
  const typeFields = dataSource.typeFields;
  const hasTypeFields = !!typeFields;
  const hasAnalysis = !!dataSource.analysis;
  const isTabular = dataSource.type === 'tabular_file';

  const content = (
    <div className="h-full p-4 space-y-4">
            {/* Full Width Description */}
            <div className="p-4 w-full bg-gray-50 rounded-xl">
              {hasAnalysis && dataSource.analysis?.contentDescription ? (
                <p className="text-sm text-gray-700">
                  {dataSource.analysis.contentDescription}
                </p>
              ) : (
                <p className="text-sm text-gray-400 italic">No description available</p>
              )}
            </div>
            
            {/* Full Width File Stats */}
            <div className="bg-gray-50 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-500/20 rounded-lg">
                  <BarChart3 size={18} className="text-gray-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">
                    {hasTypeFields ? 'File Stats' : 'Data Source Info'}
                  </h3>
                  <p className="text-xs text-gray-600 font-mono">{dataSource.type}</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">Created:</span>
                  <span className="text-sm text-gray-900 font-mono ml-2">{formatDate(dataSource.createdAt)}</span>
                </div>
                
                {hasTypeFields && typeFields && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">File Name:</span>
                      <span className="text-sm text-gray-900 font-mono">{typeFields.fileName}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">File Type:</span>
                      <span className="text-sm text-gray-900 font-mono">{typeFields.fileType}</span>
                    </div>
                    {isTabular && (
                      <>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Rows:</span>
                          <span className="text-sm text-gray-900 font-mono">{(typeFields as TabularFileDataSourceInDB).numRows.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Columns:</span>
                          <span className="text-sm text-gray-900 font-mono">{(typeFields as TabularFileDataSourceInDB).numColumns.toLocaleString()}</span>
                        </div>
                      </>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">File Size:</span>
                      <span className="text-sm text-gray-900 font-mono">
                        {(typeFields.fileSizeBytes / (1024 * 1024)).toFixed(2)} MB
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Quality Assessment and Cautions Side by Side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className={`bg-gray-50 rounded-xl p-4 space-y-3 flex flex-col ${
                hasAnalysis && dataSource.analysis?.qualityDescription
                  ? 'bg-gray-50'
                  : 'bg-gray-100'
              }`}>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="p-2 bg-gray-500/20 rounded-lg">
                    <Shield size={18} className="text-gray-600" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900">Quality Assessment</h3>
                </div>
                <div className="overflow-y-auto pr-2">
                  { hasAnalysis && dataSource.analysis?.qualityDescription ?
                    <p className="text-sm text-gray-600 leading-relaxed">{dataSource.analysis.qualityDescription}</p>
                    :
                    <div className="flex items-center justify-center h-full">
                      <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Working on it...</p>
                    </div>
                  }
                </div>
              </div>

              <div className={`bg-gray-50 rounded-xl p-4 space-y-3 flex flex-col ${
                hasAnalysis && dataSource.analysis?.cautions
                  ? 'bg-gray-50'
                  : 'bg-gray-100'
              }`}>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="p-2 bg-gray-500/20 rounded-lg">
                    <Shield size={18} className="text-gray-600" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-900">Cautions</h3>
                </div>
                <div className="overflow-y-auto pr-2">
                  {hasAnalysis && dataSource.analysis?.cautions ?
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
  );

  if (asModal) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden m-4" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-sm font-mono text-gray-900">{dataSource.name}</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-gray-500" />
            </button>
          </div>
          <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
            {content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          <div className="flex-1 min-h-0">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}