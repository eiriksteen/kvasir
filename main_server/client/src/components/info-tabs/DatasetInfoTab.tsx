import { Layers, ChevronDown, ChevronRight, Database, Calendar, Trash2 } from 'lucide-react';  
import { useEffect, useState } from 'react';
import { useDataset, useDatasets } from "@/hooks/useDatasets";
import { ObjectGroupWithObjects, DataObject, TimeSeriesInDB } from "@/types/data-objects";
import TimeSeriesChart from '@/components/charts/TimeSeriesChart';
import { UUID } from 'crypto';
import ConfirmationPopup from '@/components/ConfirmationPopup';


interface DatasetInfoTabProps {
  datasetId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
}   

type SelectedEntity = {
  id: UUID;
  type: "time_series" | "time_series_aggregation";
}


export default function DatasetInfoTab({ 
  datasetId,
  projectId,
  onClose,
  onDelete
}: DatasetInfoTabProps) {

  const { dataset, objectGroups } = useDataset(datasetId, projectId);
  const { deleteDataset } = useDatasets(projectId);
  const [selectedEntity, setSelectedEntity] = useState<SelectedEntity | null>(null);
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

  const isTimeSeries = (obj: DataObject): boolean => {
    return obj.modalityFields !== undefined && 'startTimestamp' in obj.modalityFields;
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
            <div className="h-full p-4 space-y-4 flex flex-col">
              {/* Full Width Description */}
              <div className="p-4 w-full flex items-start justify-between">
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
                  className="p-2 text-red-800 hover:bg-red-100 rounded-lg transition-colors ml-4 flex-shrink-0"
                  title="Delete dataset"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              {selectedEntity && selectedEntity.type === "time_series" ? (
                <div className="w-full flex-1">
                  <TimeSeriesChart timeSeriesId={selectedEntity.id} />
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                  {/* Right Column - Data Groups */}
                  {objectGroups && (
                    <div className="lg:col-span-2">
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
                                        const objIsTimeSeries = isTimeSeries(obj);
                                        return (
                                        <div 
                                          key={obj.id} 
                                          onClick={() => setSelectedEntity({id: obj.id, type: objIsTimeSeries ? 'time_series' : 'time_series_aggregation'})}
                                          className="group relative flex items-center gap-3 p-1 rounded-lg cursor-pointer transition-all duration-200 hover:bg-[#0E4F70]/10 hover:border-[#0E4F70]/30 border border-transparent">
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                              <div className="flex items-center gap-2">
                                                <span className="text-xs px-2 py-1 bg-gray-200 rounded-full text-gray-600 font-mono">
                                                  {objIsTimeSeries ? 'TS' : 'AGG'}
                                                </span>
                                                <span className="text-sm font-medium text-gray-900 truncate">{obj.name}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                {objIsTimeSeries && (
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