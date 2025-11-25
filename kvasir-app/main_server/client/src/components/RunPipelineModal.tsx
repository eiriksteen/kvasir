// import { X, Play, Database, Folder, Brain, Settings } from 'lucide-react';
// import { useState, useEffect, useMemo } from 'react';
import { Pipeline } from '@/types/ontology/pipeline';
import { UUID } from 'crypto';

interface RunPipelineModalProps {
  pipeline: Pipeline;
  projectId: UUID;
  isOpen: boolean;
  onClose: () => void;
  onRunPipeline: (config: {
    args: Record<string, unknown>;
    inputs: {
      dataSourceIds: UUID[];
      datasetIds: UUID[];
      modelInstantiatedIds: UUID[];
    };
    name?: string;
    description?: string;
  }) => void;
}

export default function RunPipelineModal({
  // pipeline,
  // projectId,
  // isOpen,
  // onClose,
  // onRunPipeline,
}: RunPipelineModalProps) {
  return null
  // const { getEntityGraphNode } = useProject(projectId);
  // const [runName, setRunName] = useState('');
  // const [runDescription, setRunDescription] = useState('');
  // const [selectedDataSourceIds, setSelectedDataSourceIds] = useState<UUID[]>([]);
  // const [selectedDatasetIds, setSelectedDatasetIds] = useState<UUID[]>([]);
  // const [selectedModelEntityIds, setSelectedModelEntityIds] = useState<UUID[]>([]);

  // // Get pipeline inputs from entity graph
  // const pipelineInputs = useMemo(() => {
  //   const graphNode = getEntityGraphNode(pipeline.id);
  //   return graphNode?.fromEntities || { dataSources: [], datasets: [], modelsInstantiated: [], analyses: [], pipelines: [], pipelineRuns: [] };
  // }, [pipeline.id, getEntityGraphNode]);

  // // Prevent body scroll when modal is open
  // useEffect(() => {
  //   if (isOpen) {
  //     document.body.style.overflow = 'hidden';
  //   } else {
  //     document.body.style.overflow = 'unset';
  //   }
  //   return () => {
  //     document.body.style.overflow = 'unset';
  //   };
  // }, [isOpen]);

  // // Handle escape key to close modal
  // useEffect(() => {
  //   const handleEscape = (e: KeyboardEvent) => {
  //     if (e.key === 'Escape') {
  //       onClose();
  //     }
  //   };

  //   document.addEventListener('keydown', handleEscape);
  //   return () => document.removeEventListener('keydown', handleEscape);
  // }, [onClose]);

  // // Reset selections when modal opens
  // useEffect(() => {
  //   if (isOpen) {
  //     // Pre-select all supported inputs by default
  //     setSelectedDataSourceIds(pipelineInputs.dataSources);
  //     setSelectedDatasetIds(pipelineInputs.datasets);
  //     setSelectedModelEntityIds(pipelineInputs.modelsInstantiated);
  //     setRunName('');
  //     setRunDescription('');
  //   }
  // }, [isOpen, pipelineInputs]);

  // if (!isOpen) return null;

  // const handleRun = () => {
  //   // Note: Entity relationships are managed through the entity graph
  //   // The selected inputs are passed to establish connections
  //   onRunPipeline({
  //     args: {}, // Placeholder - will be configured later
  //     inputs: {
  //       dataSourceIds: selectedDataSourceIds,
  //       datasetIds: selectedDatasetIds,
  //       modelInstantiatedIds: selectedModelEntityIds,
  //     },
  //     name: runName || undefined,
  //     description: runDescription || undefined,
  //   });
  //   onClose();
  // };

  // const toggleDataSource = (id: UUID) => {
  //   setSelectedDataSourceIds((prev) =>
  //     prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
  //   );
  // };

  // const toggleDataset = (id: UUID) => {
  //   setSelectedDatasetIds((prev) =>
  //     prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
  //   );
  // };

  // const toggleModelEntity = (id: UUID) => {
  //   setSelectedModelEntityIds((prev) =>
  //     prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
  //   );
  // };

  // const hasInputs =
  //   pipelineInputs.dataSources.length > 0 ||
  //   pipelineInputs.datasets.length > 0 ||
  //   pipelineInputs.modelsInstantiated.length > 0;

  // const hasSelections =
  //   selectedDataSourceIds.length > 0 ||
  //   selectedDatasetIds.length > 0 ||
  //   selectedModelEntityIds.length > 0;

  // return (
  //   <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  //     <div className="bg-white border border-gray-300 rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
  //       {/* Header */}
  //       <div className="flex justify-between items-start p-6 border-b border-gray-200">
  //         <div>
  //           <h3 className="text-lg font-semibold text-gray-900">Run Pipeline</h3>
  //           <p className="text-sm text-gray-600 mt-1">{pipeline.name}</p>
  //         </div>
  //         <button
  //           onClick={onClose}
  //           className="text-gray-600 hover:text-gray-900 transition-colors"
  //         >
  //           <X size={20} />
  //         </button>
  //       </div>

  //       {/* Scrollable Content */}
  //       <div className="flex-1 overflow-y-auto p-6 space-y-6">
  //         {/* Run Name & Description */}
  //         <div className="space-y-4">
  //           <div>
  //             <label className="block text-sm font-medium text-gray-700 mb-1">
  //               Run Name (Optional)
  //             </label>
  //             <input
  //               type="text"
  //               value={runName}
  //               onChange={(e) => setRunName(e.target.value)}
  //               placeholder="e.g., Production run 2024-11-02"
  //               className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#840B08]/20 focus:border-[#840B08]"
  //             />
  //           </div>
            
  //           <div>
  //             <label className="block text-sm font-medium text-gray-700 mb-1">
  //               Description (Optional)
  //             </label>
  //             <textarea
  //               value={runDescription}
  //               onChange={(e) => setRunDescription(e.target.value)}
  //               placeholder="Add any notes about this run..."
  //               rows={2}
  //               className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#840B08]/20 focus:border-[#840B08] resize-none"
  //             />
  //           </div>
  //         </div>

  //         {/* Input Selection */}
  //         {hasInputs && (
  //           <div className="space-y-3">
  //             <h4 className="text-sm font-semibold text-gray-900">Select Inputs</h4>
              
  //             {/* Data Sources */}
  //             {pipelineInputs.dataSources.length > 0 && (
  //               <div className="space-y-2">
  //                 <label className="text-xs font-medium text-gray-600 uppercase">
  //                   Data Sources
  //                 </label>
  //                 <div className="space-y-1">
  //                   {pipelineInputs.dataSources.map((id) => (
  //                     <label
  //                       key={id}
  //                       className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
  //                     >
  //                       <input
  //                         type="checkbox"
  //                         checked={selectedDataSourceIds.includes(id)}
  //                         onChange={() => toggleDataSource(id)}
  //                         className="rounded border-gray-300 text-[#840B08] focus:ring-[#840B08]"
  //                       />
  //                       <Database size={14} className="text-gray-500" />
  //                       <span className="text-sm text-gray-700">{id}</span>
  //                     </label>
  //                   ))}
  //                 </div>
  //               </div>
  //             )}

  //             {/* Datasets */}
  //             {pipelineInputs.datasets.length > 0 && (
  //               <div className="space-y-2">
  //                 <label className="text-xs font-medium text-gray-600 uppercase">
  //                   Datasets
  //                 </label>
  //                 <div className="space-y-1">
  //                   {pipelineInputs.datasets.map((id) => (
  //                     <label
  //                       key={id}
  //                       className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
  //                     >
  //                       <input
  //                         type="checkbox"
  //                         checked={selectedDatasetIds.includes(id)}
  //                         onChange={() => toggleDataset(id)}
  //                         className="rounded border-gray-300 text-[#840B08] focus:ring-[#840B08]"
  //                       />
  //                       <Folder size={14} className="text-[#0E4F70]" />
  //                       <span className="text-sm text-gray-700">{id}</span>
  //                     </label>
  //                   ))}
  //                 </div>
  //               </div>
  //             )}

  //             {/* Model Entities */}
  //             {pipelineInputs.modelsInstantiated.length > 0 && (
  //               <div className="space-y-2">
  //                 <label className="text-xs font-medium text-gray-600 uppercase">
  //                   Model Entities
  //                 </label>
  //                 <div className="space-y-1">
  //                   {pipelineInputs.modelsInstantiated.map((id) => (
  //                     <label
  //                       key={id}
  //                       className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
  //                     >
  //                       <input
  //                         type="checkbox"
  //                         checked={selectedModelEntityIds.includes(id)}
  //                         onChange={() => toggleModelEntity(id)}
  //                         className="rounded border-gray-300 text-[#840B08] focus:ring-[#840B08]"
  //                       />
  //                       <Brain size={14} className="text-[#491A32]" />
  //                       <span className="text-sm text-gray-700">{id}</span>
  //                     </label>
  //                   ))}
  //                 </div>
  //               </div>
  //             )}
  //           </div>
  //         )}

  //         {/* Configuration Placeholder */}
  //         <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
  //           <Settings size={32} className="text-gray-400 mx-auto mb-2" />
  //           <p className="text-sm text-gray-600 mb-1">Pipeline Configuration</p>
  //           <p className="text-xs text-gray-400">
  //             Advanced configuration options will be available here
  //           </p>
  //         </div>
  //       </div>

  //       {/* Footer */}
  //       <div className="border-t border-gray-200 p-6 flex justify-end gap-3">
  //         <button
  //           onClick={onClose}
  //           className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
  //         >
  //           Cancel
  //         </button>
  //         <button
  //           onClick={handleRun}
  //           disabled={!hasSelections}
  //           className="px-4 py-2 rounded-lg bg-[#840B08] text-white hover:bg-[#840B08]/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
  //         >
  //           <Play size={16} />
  //           Run Pipeline
  //         </button>
  //       </div>
  //     </div>
  //   </div>
  // );
}

