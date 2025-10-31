import { Brain, FileCode, Info, Settings, ArrowLeft, ArrowRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import { UUID } from 'crypto';
import { useModelEntity } from '@/hooks/useModelEntities';

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
            {/* Note: implementationScriptPath is now a string path, not a UUID. Code view not available. */}
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 text-sm">Code view not available - implementation uses script path instead of script ID</p>
            </div>
          </div>
        ) : (
          <div className="h-full overflow-y-auto pl-4 pr-4 pb-4 space-y-4">
            {/* Model Docstring */}
            {modelEntity?.implementation?.modelImplementation?.modelClassDocstring ? (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {modelEntity.implementation.modelImplementation.modelClassDocstring}
                </pre>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-400 italic">No documentation available</p>
              </div>
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
                      <Settings size={18} className="text-[#491A32]" />
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
                        <ArrowLeft size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Inputs</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 space-y-3">
                      <p className="text-sm text-gray-400 italic">Inputs/outputs information not available</p>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-xl p-4 space-y-3 flex flex-col">
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="p-2 bg-[#491A32]/20 rounded-lg">
                        <ArrowRight size={18} className="text-[#491A32]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Outputs</h3>
                    </div>
                    <div className="overflow-y-auto pr-2 space-y-3">
                      <p className="text-sm text-gray-400 italic">Inputs/outputs information not available</p>
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
