import { Brain, FileCode, Info, Settings, ArrowLeft, ArrowRight, Trash2, FileText } from 'lucide-react';
import { useEffect, useState } from 'react';
import { UUID } from 'crypto';
import { useModelInstantiated } from '@/hooks/useModelsInstantiated';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import JsonSchemaViewer from '@/components/JsonSchemaViewer';
import { useOntology } from '@/hooks/useOntology';

interface ModelInfoTabProps {
  modelInstantiatedId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
}

type ViewType = 'overview' | 'code';

export default function ModelInfoTab({
  modelInstantiatedId,
  projectId,
  onClose,
  onDelete
}: ModelInfoTabProps) {

  const { modelInstantiated } = useModelInstantiated(modelInstantiatedId);
  const { deleteModelInstantiated } = useOntology(projectId);
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteModelInstantiated({ modelInstantiatedId });
      onDelete?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete model instantiated:', error);
    }
  };

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

  if (!modelInstantiated) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden flex flex-col">
      {/* Top Buttons */}
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex gap-2">
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
        {modelInstantiated?.model?.implementation && (
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
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="p-2 text-red-800 hover:bg-red-100 rounded-lg transition-colors"
          title="Delete model instantiated"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {currentView === 'code' && modelInstantiated?.model?.implementation ? (
          <div className="h-full">
            {/* Note: implementationScriptPath is now a string path, not a UUID. Code view not available. */}
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 text-sm">Code view not available - implementation uses script path instead of script ID</p>
            </div>
          </div>
        ) : (
          <div className="h-full overflow-y-auto pl-4 pr-4 pb-4 space-y-4">
            {/* Model Docstring */}
            {modelInstantiated?.model?.implementation?.modelClassDocstring ? (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {modelInstantiated.model.implementation.modelClassDocstring}
                </pre>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-400 italic">No documentation available</p>
              </div>
            )}

            {!modelInstantiated.model.implementation ? (
              <div className="flex items-center justify-center h-32">
                <div className="flex items-center gap-2 text-[#491A32]/60">
                  <Brain size={20} />
                  <span className="text-sm font-medium">Implementation in progress</span>
                </div>
              </div>
            ) : (
              <>
                {/* Config Schema */}
                {modelInstantiated.model.implementation?.configSchema && Object.keys(modelInstantiated.model.implementation.configSchema).length > 0 && (
                  <div className="bg-gray-50 rounded-xl p-4 flex flex-col min-h-0">
                    <JsonSchemaViewer
                      schema={modelInstantiated.model.implementation.configSchema}
                      title="Configuration Schema"
                      icon={FileText}
                      iconColor="#491A32"
                      className="flex-1 min-h-0"
                    />
                  </div>
                )}

                {/* Configuration */}
                <div className="bg-gray-50 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#491A32]/20 rounded-lg">
                      <Settings size={18} className="text-[#491A32]" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">Configuration</h3>
                  </div>
                  <div className="space-y-2">
                    {modelInstantiated.model.implementation && Object.keys(modelInstantiated.model.implementation.defaultConfig).length > 0 ? (
                      Object.entries(modelInstantiated.model.implementation.defaultConfig).map(([key, value]) => (
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
      
      <ConfirmationPopup
        message={`Are you sure you want to delete "${modelInstantiated.name}"? This will permanently delete the model entity and all its implementations. This action cannot be undone.`}
        isOpen={showDeleteConfirm}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
