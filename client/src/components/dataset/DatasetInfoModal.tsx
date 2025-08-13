import { X, Info, Layers, Tag, Folder, ArrowLeft } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useDataset } from "@/hooks/useDatasets";
import { ObjectGroupWithObjectList, TimeSeries, TimeSeriesAggregation } from "@/types/data-objects";
import TimeSeriesEChart from '@/components/data-visualization/TimeSeriesEChart';
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
        <div className="w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden bg-black/50 rounded-lg">
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
                  <TimeSeriesEChart timeSeriesId={selectedEntity.id} />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-y-auto">
                  <div className="space-y-3">
                    <div className="border border-blue-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50">
                      <div className="flex items-center gap-2">
                        <Folder size={16} className="text-blue-400" />
                        <h3 className="text-sm text-gray-200 font-mono">Dataset</h3>
                      </div>
                      <p className="text-sm text-gray-300/80">Modality: {dataset.modality}</p>
                      <p className="text-sm text-gray-300/80">Created: {formatDate(dataset.createdAt)}</p>
                      <p className="text-sm text-gray-300/80">Updated: {formatDate(dataset.updatedAt)}</p>
                    </div>

                    {dataset.description && (
                      <div className="border border-blue-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50">
                        <div className="flex items-center gap-2">
                          <Info size={16} className="text-blue-300" />
                          <h3 className="text-sm text-gray-200 font-mono">Description</h3>
                        </div>
                        <p className="text-sm text-gray-300/80">{dataset.description}</p>
                      </div>
                    )}

                    {objectGroups && objectGroups.primaryObjectGroup?.features?.length > 0 && (
                      <div className="border border-blue-500/20 rounded-lg p-4 space-y-2 bg-zinc-900/50">
                        <div className="flex items-center gap-2">
                          <Tag size={16} className="text-blue-300" />
                          <h3 className="text-sm text-gray-200 font-mono">Features</h3>
                        </div>
                        <div className="space-y-2 max-h-[28vh] overflow-y-auto pr-1">
                          {objectGroups.primaryObjectGroup.features.map((feature) => (
                            <div key={feature.name}>
                              <p className="text-sm text-gray-300/80">{feature.name}: {feature.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {objectGroups && (
                    <div className="">
                      <div className="border border-blue-500/20 rounded-lg p-3 flex flex-col max-h-[70vh] bg-zinc-900/50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Layers size={16} className="text-blue-300" />
                            <h3 className="text-sm text-gray-200 font-mono">Raw Data</h3>
                          </div>
                        </div>

                        <div className="mt-2 space-y-1 overflow-y-auto pr-1">
                          {allGroups.map((group: ObjectGroupWithObjectList) => {
                            const isOpen = expandedGroupIds.has(group.id);
                            return (
                              <div key={group.id}>
                                <button
                                  onClick={() => toggleGroup(group.id)}
                                  className="w-full group relative flex items-center gap-2 px-1 py-4 text-sm cursor-pointer transition-all duration-150 hover:bg-blue-500/8"
                                >
                                  <span className="truncate text-gray-200 font-mono text-xs">{group.name}</span>
                                </button>
                                {isOpen && (
                                  <div className="px-0 pb-1 space-y-1 max-h-[28vh] overflow-y-auto">
                                    {group.objects?.map((obj: TimeSeries | TimeSeriesAggregation) => (
                                      <div onClick={() => setSelectedEntity({id: obj.id, type: obj.type})} key={obj.id} className="group relative flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer transition-all duration-150 hover:bg-blue-500/8">
                                        <span className="truncate text-gray-200 font-mono text-xs">{obj.name}</span>
                                      </div>
                                    ))}
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