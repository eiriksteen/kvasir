import { X, BarChart3, FileText as FileDescription, Shield, List } from 'lucide-react';
import { useEffect } from 'react';
import { useDataSource } from "@/hooks/useDataSources";
import { UUID } from 'crypto';

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

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={() => onClose()}
      />
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden bg-black/50 rounded-lg">
          <div className="rounded-xl border-2 border-emerald-500/20 shadow-xl shadow-emerald-500/10 h-full flex flex-col">
            <div className="relative flex items-center p-4 border-b border-emerald-500/20 flex-shrink-0">
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
                {/* Left Column - File Stats & Features */}
                <div className="lg:col-span-1 flex flex-col space-y-4 max-h-[100vh] overflow-y-auto">
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <BarChart3 size={18} className="text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-200">File Stats</h3>
                        <p className="text-xs text-gray-400 font-mono">{dataSource.fileType}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300/80">File Size:</span>
                        <span className="text-sm text-gray-200 font-mono">{dataSource.fileSizeBytes} bytes</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300/80">Created:</span>
                        <span className="text-sm text-gray-200 font-mono">{formatDate(dataSource.createdAt)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300/80">Rows:</span>
                        <span className="text-sm text-gray-200 font-mono">{dataSource.numRows}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300/80">Columns:</span>
                        <span className="text-sm text-gray-200 font-mono">{dataSource.numColumns}</span>
                      </div>
                    </div>
                  </div>

                  {dataSource.features && dataSource.features.length > 0 && (
                    <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                          <List size={18} className="text-emerald-300" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-200">Features</h3>
                        <span className="text-xs px-2 py-1 bg-emerald-500/20 rounded-full text-emerald-300 font-mono">
                          {dataSource.features.length} feature(s)
                        </span>
                      </div>
                      <div className="space-y-2 overflow-y-auto pr-2 flex-1 min-h-0">
                        {dataSource.features.map((feature) => (
                          <div key={feature.name} className="bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/50">
                            <div className="flex justify-between items-start mb-1">
                              <span className="text-sm font-medium text-gray-200">{feature.name}</span>
                            </div>
                            <p className="text-xs text-gray-400">{feature.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Column - Quality & Description */}
                <div className="lg:col-span-1 flex flex-col space-y-4 max-h-[100vh] overflow-y-auto">

                  {dataSource.description && (
                    <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                          <FileDescription size={18} className="text-emerald-300" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-200">Content Description</h3>
                      </div>
                      <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                        <p className="text-sm text-gray-300/80 leading-relaxed">{dataSource.description}</p>
                      </div>
                    </div>
                  )}

                  {dataSource.qualityDescription && (
                    <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                          <Shield size={18} className="text-emerald-300" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-200">Quality Description</h3>
                      </div>
                      <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                        <p className="text-sm text-gray-300/80 leading-relaxed">{dataSource.qualityDescription}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}