import { X, Brain } from 'lucide-react';
import { useEffect } from 'react';
import { UUID } from 'crypto';
import { useModelEntity } from '@/hooks/useModelEntities';

interface ModelInfoModalProps {
  modelEntityId: UUID;
  projectId: UUID;
  onClose: () => void;
}

export default function ModelInfoModal({
  modelEntityId,
  projectId,
  onClose
}: ModelInfoModalProps) {

  const { modelEntity } = useModelEntity(projectId, modelEntityId);

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

  if (!modelEntity) {
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
                  {modelEntity.name}
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
                {/* Left Column - Model Stats */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <Brain size={18} className="text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-200">
                          Model Information
                        </h3>
                        <p className="text-xs text-gray-400 font-mono">{modelEntity.model.task}</p>
                      </div>
                    </div>
                    <div className="space-y-2 flex-1 overflow-y-auto pr-2 min-h-0">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-300/80">Created:</span>
                        <span className="text-sm text-gray-200 font-mono ml-2">{formatDate(modelEntity.createdAt)}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-300/80">Updated:</span>
                        <span className="text-sm text-gray-200 font-mono ml-2">{formatDate(modelEntity.updatedAt)}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-300/80">Modality:</span>
                        <span className="text-sm text-gray-200 font-mono ml-2">{modelEntity.model.modality}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-300/80">Language:</span>
                        <span className="text-sm text-gray-200 font-mono ml-2">{modelEntity.model.programmingLanguageWithVersion}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <Brain size={18} className="text-emerald-400" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Description</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <p className="text-sm text-gray-300/80 leading-relaxed">{modelEntity.description}</p>
                    </div>
                  </div>
                </div>

                {/* Right Column - Additional Information */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <Brain size={18} className="text-emerald-400" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Configuration</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-gray-400/80 leading-relaxed text-center font-medium">Coming soon...</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-emerald-500/20 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-emerald-500/20 rounded-lg">
                        <Brain size={18} className="text-emerald-400" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Training Details</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-gray-400/80 leading-relaxed text-center font-medium">Coming soon...</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
