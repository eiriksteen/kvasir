import { Layers, ChevronDown, ChevronRight, Database, Calendar, Trash2, Settings } from 'lucide-react';  
import { useEffect, useState } from 'react';
import { useDataset, useDatasets } from "@/hooks/useDatasets";
import { ObjectGroupWithObjects, DataObject, TimeSeriesInDB, Modality } from "@/types/data-objects";
import TimeSeriesChart from '@/components/charts/TimeSeriesChart';
import { UUID } from 'crypto';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import JsonViewer from '@/components/JsonViewer';


interface DatasetInfoTabProps {
  datasetId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
}   

type SelectedDataObject = {
  id: UUID;
  modality: Modality;
  startTimestamp: string;
  endTimestamp: string;
}


export default function DatasetInfoTab({ 
  datasetId,
  projectId,
  onClose,
  onDelete
}: DatasetInfoTabProps) {

  const { dataset, objectGroups } = useDataset(datasetId, projectId);
  const { deleteDataset } = useDatasets(projectId);
  const [selectedDataObject, setSelectedDataObject] = useState<SelectedDataObject | null>(null);
  const [expandedGroupIds, setExpandedGroupIds] = useState<Set<string>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteDataset({ datasetId });
      onDelete?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete dataset:', error);
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

  const toggleGroup = (groupId: string) => {
    setExpandedGroupIds(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) next.delete(groupId); else next.add(groupId);
      return next;
    });
  };

  const formatTimeRange = (obj: DataObject) => {
    const fields = obj.modalityFields as TimeSeriesInDB;
    const start = new Date(fields.startTimestamp).toLocaleDateString();
    const end = new Date(fields.endTimestamp).toLocaleDateString();
    return `${start} - ${end}`;
  };

  if (!dataset) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden flex flex-col">
      <div className="bg-white h-full px-0 pb-2 relative flex flex-col overflow-hidden">
        <div className="flex-1 min-h-0 overflow-y-auto flex flex-col">
          {/* Content Section */}
          <div className="flex-1 min-h-0 flex flex-col">
            <div className="h-full p-4 flex flex-col">
              {/* Full Width Description */}
              <div className="w-full flex items-start justify-between pb-4">
                <div className="flex-1">
                  {dataset.description ? (
                    <p className="text-sm text-gray-700">
                      {dataset.description}
                    </p>
                  ) : (
                    <p className="text-sm text-gray-400 italic">No description provided</p>
                  )}
                </div>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="text-red-800 hover:bg-red-100 rounded-lg transition-colors ml-4 flex-shrink-0"
                  title="Delete dataset"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              {selectedDataObject && selectedDataObject.modality === "time_series" ? (
                <div className="w-full flex-1">
                  <TimeSeriesChart 
                    request={{
                      projectId,
                      objectId: selectedDataObject.id,
                      args: {
                        startTimestamp: selectedDataObject.startTimestamp,
                        endTimestamp: selectedDataObject.endTimestamp
                      }
                    }}
                  />
                </div>
              ) : (
                <div className={`flex gap-4 h-full ${dataset.additionalVariables && Object.keys(dataset.additionalVariables).length > 0 ? 'flex-row' : ''}`}>
                  {/* Left Column - Additional Variables */}
                  {dataset.additionalVariables && Object.keys(dataset.additionalVariables).length > 0 && (
                    <div className="flex-shrink-0 w-96">
                      <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 h-full flex flex-col">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="p-2 bg-purple-500/20 rounded-lg">
                            <Settings size={18} className="text-purple-700" />
                          </div>
                          <h3 className="text-sm font-semibold text-gray-900">Additional Variables</h3>
                        </div>
                        <div className="flex-1 overflow-hidden">
                          <JsonViewer data={dataset.additionalVariables} className="h-full" />
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Right Column - Data Groups */}
                  {objectGroups && (
                    <div className="flex-1 min-w-0">
                      <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 h-full flex flex-col">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="p-2 bg-[#0E4F70]/20 rounded-lg">
                            <Layers size={18} className="text-[#0E4F70]" />
                          </div>
                          <h3 className="text-sm font-semibold text-gray-900">Data Groups</h3>
                          <span className="text-xs px-2 py-1 bg-[#0E4F70]/20 rounded-full text-[#0E4F70] font-mono">
                            {objectGroups?.length || 0}
                          </span>
                        </div>

                        <div className="flex-1 space-y-1 overflow-y-auto pr-2">
                          {objectGroups.map((group: ObjectGroupWithObjects) => {
                            const isOpen = expandedGroupIds.has(group.id);
                            const entityCount = group.objects?.length || 0;
                            
                            return (
                              <div key={group.id} className="bg-gray-100 rounded-xl border border-gray-300 overflow-hidden">
                                <button
                                  onClick={() => toggleGroup(group.id)}
                                  className="w-full group relative flex items-center justify-between p-2 text-sm cursor-pointer transition-all duration-200 hover:bg-gray-100"
                                >
                                  <div className="flex items-center gap-3">
                                    <div className="p-2 bg-gray-200 rounded-lg group-hover:bg-gray-300 transition-colors">
                                      <Layers size={16} className="text-gray-600" />
                                    </div>
                                    <div className="text-left">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium text-gray-900">{group.name}</span>
                                      </div>
                                      <p className="text-xs text-gray-600">{group.description}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs px-2 py-1 bg-gray-200 rounded-full text-gray-600 font-mono">
                                      {entityCount}
                                    </span>
                                    {isOpen ? (
                                      <ChevronDown size={16} className="text-gray-600 group-hover:text-gray-900 transition-colors" />
                                    ) : (
                                      <ChevronRight size={16} className="text-gray-600 group-hover:text-gray-900 transition-colors" />
                                    )}
                                  </div>
                                </button>
                                
                                {isOpen && (
                                  <div className="border-t border-gray-300 bg-gray-50">
                                    <div className="p-2 space-y-2">
                                      {group.objects?.map((obj: DataObject) => {
                                        const modality = objectGroups.find(group => group.id === obj.groupId)?.modality;
                                        const hasRawDataFn = objectGroups.find(group => group.id === obj.groupId)?.rawDataReadScriptPath !== null;
                                        const modalityFields = obj.modalityFields as TimeSeriesInDB;
                                        const onClick = hasRawDataFn ? () => setSelectedDataObject({
                                          id: obj.id, 
                                          modality: modality as Modality,
                                          startTimestamp: modalityFields.startTimestamp,
                                          endTimestamp: modalityFields.endTimestamp
                                        }) : undefined;
                                        return (
                                        <div 
                                          key={obj.id} 
                                          onClick={onClick}
                                          className={`group relative flex items-center gap-3 p-1 rounded-lg transition-all duration-200 border border-transparent ${hasRawDataFn ? 'cursor-pointer hover:bg-[#0E4F70]/10 hover:border-[#0E4F70]/30' : 'opacity-50 cursor-default'}`}> 
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                              <div className="flex items-center gap-2">
                                                <span className="text-xs px-2 py-1 bg-gray-200 rounded-full text-gray-600 font-mono">
                                                  {modality}
                                                </span>
                                                <span className="text-sm font-medium text-gray-900 truncate">{obj.name}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                {modality === 'time_series' && (
                                                  <>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-gray-300 rounded-full text-gray-600">
                                                      <Calendar size={12} />
                                                      <span>{formatTimeRange(obj)}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-gray-300 rounded-full text-gray-600">
                                                      <Database size={12} />
                                                      <span>{(obj.modalityFields as TimeSeriesInDB).numTimestamps} points</span>
                                                    </div>
                                                  </>
                                                )}
                                              </div>
                                            </div>
                                            <p className="text-xs text-gray-600 truncate">{obj.description}</p>
                                          </div>
                                        </div>
                                      );
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <ConfirmationPopup
        message={`Are you sure you want to delete "${dataset.name}"? This will permanently delete the dataset and all its data. This action cannot be undone.`}
        isOpen={showDeleteConfirm}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}