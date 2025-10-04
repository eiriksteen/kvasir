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
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Header Section */}
          <div className="relative flex items-center p-4 border-b border-gray-300 flex-shrink-0">
            <div className="ml-2">
              <h3 className="text-sm font-mono tracking-wider text-gray-900">
                {modelEntity.name}
              </h3>
            </div>
            <button
              onClick={() => onClose()}
              className="absolute right-6 text-gray-500 hover:text-gray-700 transition-colors"
              title="Close tab"
            >
              <X size={20} />
            </button>
          </div>
          
          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full p-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {/* Left Column - Model Stats */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-900">
                          Model Information
                        </h3>
                        <p className="text-xs text-gray-600 font-mono">{modelEntity.model.task}</p>
                      </div>
                    </div>
                    <div className="space-y-2 flex-1 overflow-y-auto pr-2 min-h-0">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600">Created:</span>
                        <span className="text-sm text-gray-900 font-mono ml-2">{formatDate(modelEntity.createdAt)}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600">Updated:</span>
                        <span className="text-sm text-gray-900 font-mono ml-2">{formatDate(modelEntity.updatedAt)}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600">Modality:</span>
                        <span className="text-sm text-gray-900 font-mono ml-2">{modelEntity.model.modality}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-600">Language:</span>
                        <span className="text-sm text-gray-900 font-mono ml-2">{modelEntity.model.programmingLanguageWithVersion}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Description</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <p className="text-sm text-gray-600 leading-relaxed">{modelEntity.description}</p>
                    </div>
                  </div>
                </div>

                {/* Right Column - Additional Information */}
                <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto">
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Configuration</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Coming soon...</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 space-y-3 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Training Details</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 flex-1 min-h-0">
                      <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-gray-600 leading-relaxed text-center font-medium">Coming soon...</p>
                      </div>
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
