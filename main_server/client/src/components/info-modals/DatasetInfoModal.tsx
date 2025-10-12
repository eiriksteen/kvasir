import { X, Layers, ArrowLeft, ChevronDown, ChevronRight, Database, Calendar, List } from 'lucide-react';  
import { useEffect, useState } from 'react';
import { useDataset } from "@/hooks/useDatasets";
import { ObjectGroupWithObjectList, TimeSeries, TimeSeriesAggregation } from "@/types/data-objects";
import TimeSeriesChart from '@/components/charts/TimeSeriesChart';
import { UUID } from 'crypto';


interface DatasetInfoModalProps {
  datasetId: UUID;
  projectId: UUID;
  onClose: () => void;
}   

type SelectedEntity = {
  id: UUID;
  type: "time_series" | "time_series_aggregation";
}


export default function DatasetInfoModal({ 
  datasetId,
  projectId,
  onClose
}: DatasetInfoModalProps) {

  const { dataset, objectGroups } = useDataset(datasetId, projectId);
  const [selectedEntity, setSelectedEntity] = useState<SelectedEntity | null>(null);
  const [expandedGroupIds, setExpandedGroupIds] = useState<Set<string>>(new Set());

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

  const toggleGroup = (groupId: string) => {
    setExpandedGroupIds(prev => {
      const next = new Set(prev);
      if (next.has(groupId)) next.delete(groupId); else next.add(groupId);
      return next;
    });
  };

  const formatTimeRange = (obj: TimeSeries) => {
    const start = new Date(obj.startTimestamp).toLocaleDateString();
    const end = new Date(obj.endTimestamp).toLocaleDateString();
    return `${start} - ${end}`;
  };

  if (!dataset) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Header Section */}
          <div className="relative flex items-center p-4 border-b border-gray-300 flex-shrink-0">
            <div className="ml-2 flex-1">
              {dataset.description && (
                <p className="text-xs text-gray-600 mt-1">
                  {dataset.description} • Created on {formatDate(dataset.createdAt)}
                </p>
              )}
            </div>
          </div>
          
          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full p-4">
              {selectedEntity && selectedEntity.type === "time_series" ? (
                <div className="w-full h-full">
                  <TimeSeriesChart timeSeriesId={selectedEntity.id} />
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
                  {/* Left Column - Features */}
                  <div className="lg:col-span-1 flex flex-col space-y-4 overflow-y-auto">
                    {objectGroups && objectGroups[0].features?.length > 0 && (
                      <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="p-2 bg-[#0E4F70]/20 rounded-lg">
                            <List size={18} className="text-[#0E4F70]" />
                          </div>
                          <h3 className="text-sm font-semibold text-gray-900">Features</h3>
                          <span className="text-xs px-2 py-1 bg-[#0E4F70]/20 rounded-full text-[#0E4F70] font-mono">
                            {objectGroups[0].features.length} feature(s)
                          </span>
                        </div>
                        <div className="space-y-2 overflow-y-auto pr-2 flex-1 min-h-0">
                          {objectGroups[0].features.map((feature) => (
                            <div key={feature.name} className="bg-gray-100 rounded-lg p-2 border border-gray-300">
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-sm font-medium text-gray-900">{feature.name}</span>
                              </div>
                              <p className="text-xs text-gray-600">{feature.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

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
                            {objectGroups.length} group(s)
                          </span>
                        </div>

                        <div className="flex-1 space-y-1 overflow-y-auto pr-2">
                          {objectGroups.map((group: ObjectGroupWithObjectList) => {
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
                                  <div className="border-t border-gray-300 bg-zinc-800/30">
                                    <div className="p-2 space-y-2">
                                      {group.objects?.map((obj: TimeSeries | TimeSeriesAggregation) => (
                                        <div 
                                          key={obj.id} 
                                          onClick={() => setSelectedEntity({id: obj.id, type: obj.type})}
                                          className="group relative flex items-center gap-3 p-1 rounded-lg cursor-pointer transition-all duration-200 hover:bg-[#0E4F70]/10 hover:border-[#0E4F70]/30 border border-transparent">
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                              <div className="flex items-center gap-2">
                                                <span className="text-xs px-2 py-1 bg-gray-200 rounded-full text-gray-600 font-mono">
                                                  {obj.type === 'time_series' ? 'TS' : 'AGG'}
                                                </span>
                                                <span className="text-sm font-medium text-gray-900 truncate">{obj.name}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                {obj.type === 'time_series' && (
                                                  <>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-gray-300 rounded-full text-gray-600">
                                                      <Calendar size={12} />
                                                      <span>{formatTimeRange(obj)}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-gray-300 rounded-full text-gray-600">
                                                      <Database size={12} />
                                                      <span>{obj.numTimestamps} points</span>
                                                    </div>
                                                  </>
                                                )}
                                              </div>
                                            </div>
                                            <p className="text-xs text-gray-600 truncate">{obj.description}</p>
                                          </div>
                                        </div>
                                      ))}
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
    </div>
  );
}