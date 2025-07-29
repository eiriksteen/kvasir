import { DataSource } from "@/types/data-integration";
import { X, BarChart3, FileText as FileDescription, Shield, List } from 'lucide-react';
import { useEffect } from 'react';
import { getSourceTypeIcon } from "@/lib/data-sources/sourceTypes";

export default function FileInfoModal({ 
  dataSource, 
  setSelectedDataSource 
}: { 
  dataSource: DataSource; 
  setSelectedDataSource: (dataSource: DataSource | null) => void; 
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
        setSelectedDataSource(null);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [setSelectedDataSource]);

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
        onClick={() => setSelectedDataSource(null)}
      />
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="w-full max-w-4xl flex flex-col overflow-hidden shadow-2xl">
          <div className="bg-[#0a101c]/50 border border-[#1f2937] rounded-lg">
            <div className="relative flex items-center p-3 border-b border-[#101827] flex-shrink-0">
              {getSourceTypeIcon(dataSource.type, 16)}
              <div className="ml-2">
                <h3 className="text-sm font-mono uppercase tracking-wider text-zinc-200">
                  {dataSource.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedDataSource(null)}
                className="absolute right-6 text-zinc-400 hover:text-zinc-300 transition-colors"
                title="Close modal"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-3">
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <BarChart3 size={16} className="text-blue-400" />
                  <h3 className="text-sm text-zinc-200">Stats</h3>
                </div>
                <p className="text-sm text-zinc-400">File Type: {dataSource.fileType}</p>
                <p className="text-sm text-zinc-400">File Size (bytes): {dataSource.fileSizeBytes}</p>
                <p className="text-sm text-zinc-400">Created: {formatDate(dataSource.createdAt)}</p>
                <p className="text-sm text-zinc-400">Number of Rows: {dataSource.numRows}</p>
                <p className="text-sm text-zinc-400">Number of Columns: {dataSource.numColumns}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {dataSource.description && (
                  <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <FileDescription size={16} className="text-green-400" />
                      <h3 className="text-sm text-zinc-200">Content Description</h3>
                    </div>
                    <p className="text-sm text-zinc-400">{dataSource.description}</p>
                  </div>
                )}
                {dataSource.qualityDescription && (
                  <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <Shield size={16} className="text-yellow-400" />
                      <h3 className="text-sm text-zinc-200">Quality Description</h3>
                    </div>
                    <p className="text-sm text-zinc-400">{dataSource.qualityDescription}</p>
                  </div>
                )}
              </div>
              {dataSource.features && dataSource.features.length > 0 && (
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <List size={16} className="text-purple-400" />
                    <h3 className="text-sm text-zinc-200">Features</h3>
                  </div>
                  <div className="space-y-2">
                    {dataSource.features.map((feature) => (
                      <div key={feature.name} className="">
                        <p className="text-sm text-zinc-400">{feature.name}: {feature.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}