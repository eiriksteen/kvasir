import { DataSource } from "@/types/data-sources";
import { X, BarChart3, FileText as FileDescription, Shield, List } from 'lucide-react';
import { useEffect } from 'react';

export default function FileInfoModal({ 
  dataSource, 
  onClose
}: { 
  dataSource: DataSource; 
  onClose: () => void; 
}) {
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
              <div className="space-y-3">
                <div className="border border-emerald-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50">
                  <div className="flex items-center gap-2">
                    <BarChart3 size={16} className="text-emerald-400" />
                    <h3 className="text-sm text-gray-200 font-mono">Stats</h3>
                  </div>
                  <p className="text-sm text-gray-300/80">File Type: {dataSource.fileType}</p>
                  <p className="text-sm text-gray-300/80">File Size (bytes): {dataSource.fileSizeBytes}</p>
                  <p className="text-sm text-gray-300/80">Created: {formatDate(dataSource.createdAt)}</p>
                  <p className="text-sm text-gray-300/80">Number of Rows: {dataSource.numRows}</p>
                  <p className="text-sm text-gray-300/80">Number of Columns: {dataSource.numColumns}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dataSource.description && (
                    <div className="border border-emerald-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50 max-h-[20vh] overflow-y-auto">
                      <div className="flex items-center gap-2">
                        <FileDescription size={16} className="text-emerald-300" />
                        <h3 className="text-sm text-gray-200 font-mono">Content Description</h3>
                      </div>
                      <p className="text-sm text-gray-300/80">{dataSource.description}</p>
                    </div>
                  )}
                  {dataSource.qualityDescription && (
                    <div className="border border-emerald-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50 max-h-[20vh] overflow-y-auto">
                      <div className="flex items-center gap-2">
                        <Shield size={16} className="text-emerald-300" />
                        <h3 className="text-sm text-gray-200 font-mono">Quality Description</h3>
                      </div>
                      <p className="text-sm text-gray-300/80">{dataSource.qualityDescription}</p>
                    </div>
                  )}
                </div>

                {dataSource.features && dataSource.features.length > 0 && (
                  <div className="border border-emerald-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50">
                    <div className="flex items-center gap-2">
                      <List size={16} className="text-emerald-300" />
                      <h3 className="text-sm text-gray-200 font-mono">Features</h3>
                    </div>
                    <div className="space-y-2 max-h-[20vh] overflow-y-auto">
                      {dataSource.features.map((feature) => (
                        <div key={feature.name}>
                          <p className="text-sm text-gray-300/80">{feature.name}: {feature.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}