import { Brain, FileCode, Info } from 'lucide-react';
import { useEffect, useState } from 'react';
import { UUID } from 'crypto';
import { useModelEntity } from '@/hooks/useModelEntities';
import CodeImplementation from '@/components/code/CodeImplementation';

interface ModelInfoTabProps {
  modelEntityId: UUID;
  projectId: UUID;
  onClose: () => void;
}

type ViewType = 'overview' | 'code';

export default function ModelInfoTab({
  modelEntityId,
  projectId,
  onClose
}: ModelInfoTabProps) {

  const { modelEntity } = useModelEntity(projectId, modelEntityId);
  const [currentView, setCurrentView] = useState<ViewType>('overview');

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

  if (!modelEntity) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden flex flex-col">
      {/* Top Buttons */}
      <div className="flex gap-2 px-4 py-4">
        <button
          onClick={() => setCurrentView('overview')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            currentView === 'overview'
              ? 'bg-[#491A32] text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Info className="w-4 h-4" />
          <span className="text-sm font-medium">Overview</span>
        </button>
        {modelEntity?.implementation && (
          <button
            onClick={() => setCurrentView('code')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              currentView === 'code'
                ? 'bg-[#491A32] text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span className="text-sm font-medium">Code</span>
          </button>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {currentView === 'code' && modelEntity?.implementation ? (
          <div className="h-full">
            <CodeImplementation scriptId={modelEntity.implementation.modelImplementation.implementationScript?.id || undefined} />
          </div>
        ) : (
          <div className="h-full overflow-y-auto pl-4 pr-4 pb-4 space-y-4">
            {/* Description */}
            {modelEntity.description ? (
              <p className="text-sm text-gray-700">
                {modelEntity.description}
              </p>
            ) : (
              <p className="text-sm text-gray-400 italic">No description available</p>
            )}

            {!modelEntity.implementation ? (
              <div className="flex items-center justify-center h-32">
                <div className="flex items-center gap-2 text-[#491A32]/60">
                  <Brain size={20} />
                  <span className="text-sm font-medium">Implementation in progress</span>
                </div>
              </div>
            ) : (
              <>
                {/* Configuration */}
                <div className="bg-gray-50 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#491A32]/20 rounded-lg">
                      <Brain size={18} className="text-[#491A32]" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">Configuration</h3>
                  </div>
                  <div className="space-y-2">
                    {modelEntity.implementation && Object.keys(modelEntity.implementation.config).length > 0 ? (
                      Object.entries(modelEntity.implementation.config).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">{key}:</span>
                          <span className="text-sm text-gray-900 font-mono">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-400 italic">No configuration set</p>
                    )}
                  </div>
                </div>

                {/* Inputs and Outputs Side by Side */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-xl p-4 space-y-3 flex flex-col">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Inputs</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 space-y-3">
                      {modelEntity.implementation?.modelImplementation?.inferenceFunction?.inputObjectGroups?.length > 0 ? (
                        modelEntity.implementation.modelImplementation.inferenceFunction.inputObjectGroups.map((input) => (
                          <div key={input.id} className="border-l-2 border-[#491A32]/30 pl-3">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900">{input.name}</span>
                            </div>
                            <p className="text-xs text-gray-600 font-mono mb-1">{input.structureId}</p>
                            {input.description && (
                              <p className="text-xs text-gray-600">{input.description}</p>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-400 italic">No inputs defined</p>
                      )}
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-xl p-4 space-y-3 flex flex-col">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <Brain size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Outputs</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 space-y-3">
                      {modelEntity.implementation?.modelImplementation?.inferenceFunction?.outputObjectGroups?.length > 0 ? (
                        modelEntity.implementation.modelImplementation.inferenceFunction.outputObjectGroups.map((output) => (
                          <div key={output.id} className="border-l-2 border-[#491A32]/30 pl-3">
                            {output.name && (
                              <span className="text-sm font-semibold text-gray-900">{output.name}</span>
                            )}
                            <p className="text-xs text-gray-600 font-mono mb-1">{output.structureId}</p>
                            {output.description && (
                              <p className="text-xs text-gray-600">{output.description}</p>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-400 italic">No outputs defined</p>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
