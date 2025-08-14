import { X, Layers, Tag, Folder, ArrowLeft, ChevronDown, ChevronRight, Database, BarChart3, Calendar, List } from 'lucide-react';  
import { useEffect, useMemo, useState } from 'react';
import { useDataset } from "@/hooks/useDatasets";
import { ObjectGroupWithObjectList, TimeSeries, TimeSeriesAggregation } from "@/types/data-objects";
import TimeSeriesChart from '@/components/charts/TimeSeriesChart';
import { UUID } from 'crypto';


interface DatasetInfoModalProps {
  datasetId: string;
  onClose: () => void;
}   

type SelectedEntity = {
  id: UUID;
  type: "time_series" | "time_series_aggregation";
}


export default function DatasetInfoModal({ 
  datasetId,
  onClose
}: DatasetInfoModalProps) {

  const { dataset, objectGroups } = useDataset(datasetId);
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

  const getGroupIcon = (role: string) => {
    switch (role) {
      case 'primary': return <Database size={16} className="text-blue-400" />;
      case 'annotated': return <Tag size={16} className="text-green-400" />;
      case 'derived': return <BarChart3 size={16} className="text-purple-400" />;
      default: return <Layers size={16} className="text-gray-400" />;
    }
  };

  const formatTimeRange = (obj: TimeSeries) => {
    const start = new Date(obj.startTimestamp).toLocaleDateString();
    const end = new Date(obj.endTimestamp).toLocaleDateString();
    return `${start} - ${end}`;
  };

  const allGroups = useMemo(() => {
    if (!objectGroups) return [] as ObjectGroupWithObjectList[];
    const groups: ObjectGroupWithObjectList[] = [];
    
    // Start with primary group
    if (objectGroups.primaryObjectGroup) {
      groups.push(objectGroups.primaryObjectGroup);
    }
    
    // Add annotated groups
    if (objectGroups.annotatedObjectGroups) {
      groups.push(...objectGroups.annotatedObjectGroups);
    }
    
    // Add computed groups
    if (objectGroups.computedObjectGroups) {
      groups.push(...objectGroups.computedObjectGroups);
    }
    
    return groups;
  }, [objectGroups]);

  if (!dataset) {
    return null;
  }

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={() => onClose()}
      />
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden bg-black/50 rounded-lg">
          <div className="rounded-xl border-2 border-blue-500/20 shadow-xl shadow-blue-500/10 h-full flex flex-col">
            <div className="relative flex items-center p-4 border-b border-blue-500/20 flex-shrink-0">
              <button
                onClick={() => selectedEntity && setSelectedEntity(null)}
                disabled={!selectedEntity}
                className={`mr-3 text-gray-400 transition-colors ${
                  selectedEntity 
                    ? 'hover:text-white cursor-pointer' 
                    : 'opacity-50 cursor-not-allowed'
                }`}
                title={selectedEntity ? "Go back" : "No entity selected"}
              >
                <ArrowLeft size={20} />
              </button>
              <div className="ml-2">
                <h3 className="text-sm font-mono tracking-wider text-gray-200">
                  {dataset.name}
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
            <div className="p-4 flex-1 overflow-hidden">
              {selectedEntity && selectedEntity.type === "time_series" ? (
                <div className="w-full h-full">
                  <TimeSeriesChart timeSeriesId={selectedEntity.id} />
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
                  {/* Left Column - Dataset Info */}
                  <div className="lg:col-span-1 flex flex-col space-y-4 overflow-y-auto">
                    <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-blue-500/20 rounded-xl p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                          <Folder size={18} className="text-blue-400" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-200">Dataset Info</h3>
                      </div>
                      {dataset.description && (
                        <p className="text-sm text-gray-300/80 leading-relaxed">{dataset.description} Created on {formatDate(dataset.createdAt)}</p>
                      )}
                    </div>

                    {objectGroups && objectGroups.primaryObjectGroup?.features?.length > 0 && (
                      <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-blue-500/20 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="p-2 bg-blue-500/20 rounded-lg">
                            <List size={18} className="text-blue-300" />
                          </div>
                          <h3 className="text-sm font-semibold text-gray-200">Features</h3>
                          <span className="text-xs px-2 py-1 bg-blue-500/20 rounded-full text-blue-300 font-mono">
                            {objectGroups.primaryObjectGroup.features.length} feature(s)
                          </span>
                        </div>
                        <div className="space-y-2 overflow-y-auto pr-2 flex-1 min-h-0">
                          {objectGroups.primaryObjectGroup.features.map((feature) => (
                            <div key={feature.name} className="bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/50">
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-sm font-medium text-gray-200">{feature.name}</span>
                              </div>
                              <p className="text-xs text-gray-400">{feature.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column - Data Groups */}
                  {objectGroups && (
                    <div className="lg:col-span-2">
                      <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-blue-500/20 rounded-xl p-4 h-full flex flex-col">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="p-2 bg-blue-500/20 rounded-lg">
                            <Layers size={18} className="text-blue-300" />
                          </div>
                          <h3 className="text-sm font-semibold text-gray-200">Data Groups</h3>
                          <span className="text-xs px-2 py-1 bg-blue-500/20 rounded-full text-blue-300 font-mono">
                            {allGroups.length} group(s)
                          </span>
                        </div>

                        <div className="flex-1 space-y-1 overflow-y-auto pr-2">
                          {allGroups.map((group: ObjectGroupWithObjectList) => {
                            const isOpen = expandedGroupIds.has(group.id);
                            const entityCount = group.objects?.length || 0;
                            
                            return (
                              <div key={group.id} className="bg-zinc-800/50 rounded-xl border border-zinc-700/50 overflow-hidden">
                                <button
                                  onClick={() => toggleGroup(group.id)}
                                  className="w-full group relative flex items-center justify-between p-2 text-sm cursor-pointer transition-all duration-200 hover:bg-zinc-700/30"
                                >
                                  <div className="flex items-center gap-3">
                                    <div className="p-2 bg-zinc-700/50 rounded-lg group-hover:bg-zinc-600/50 transition-colors">
                                      {getGroupIcon(group.role)}
                                    </div>
                                    <div className="text-left">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium text-gray-200">{group.name}</span>
                                      </div>
                                      <p className="text-xs text-gray-400">{group.description}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs px-2 py-1 bg-zinc-700/50 rounded-full text-gray-300 font-mono">
                                      {entityCount}
                                    </span>
                                    {isOpen ? (
                                      <ChevronDown size={16} className="text-gray-400 group-hover:text-gray-200 transition-colors" />
                                    ) : (
                                      <ChevronRight size={16} className="text-gray-400 group-hover:text-gray-200 transition-colors" />
                                    )}
                                  </div>
                                </button>
                                
                                {isOpen && (
                                  <div className="border-t border-zinc-700/50 bg-zinc-800/30">
                                    <div className="p-2 space-y-2">
                                      {group.objects?.map((obj: TimeSeries | TimeSeriesAggregation) => (
                                        <div 
                                          key={obj.id} 
                                          onClick={() => setSelectedEntity({id: obj.id, type: obj.type})}
                                          className="group relative flex items-center gap-3 p-1 rounded-lg cursor-pointer transition-all duration-200 hover:bg-blue-500/10 hover:border-blue-500/30 border border-transparent">
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                              <div className="flex items-center gap-2">
                                                <span className="text-xs px-2 py-1 bg-zinc-700/50 rounded-full text-gray-300 font-mono">
                                                  {obj.type === 'time_series' ? 'TS' : 'AGG'}
                                                </span>
                                                <span className="text-sm font-medium text-gray-200 truncate">{obj.name}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                {obj.type === 'time_series' && (
                                                  <>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-zinc-700/50 rounded-full text-gray-300">
                                                      <Calendar size={12} />
                                                      <span>{formatTimeRange(obj)}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs px-2 py-1 border border-zinc-700/50 rounded-full text-gray-300">
                                                      <Database size={12} />
                                                      <span>{obj.numTimestamps} points</span>
                                                    </div>
                                                  </>
                                                )}
                                              </div>
                                            </div>
                                            <p className="text-xs text-gray-400 truncate">{obj.description}</p>
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
    </>
  );
}