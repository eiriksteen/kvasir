import { TimeSeriesDataset, EntityMetadata } from '@/types/datasets';
import { format } from 'date-fns';
import { Database, BarChart2, Clock, Layers, Info, X, LineChart, ArrowLeft } from 'lucide-react';
import { useState } from 'react';
import { useTimeSeriesDataset } from '@/hooks/useTimeSeriesDataset';
import TimeSeriesEChart from './TimeSeriesEChart';

interface TimeSeriesVisualizerProps {
  datasetId: string;
  mode: "compact" | "full";
  onClick?: () => void;
  onClose?: () => void;
}

interface CompactViewProps extends TimeSeriesVisualizerProps {
  dataset: TimeSeriesDataset | undefined;
}

interface FullViewProps extends TimeSeriesVisualizerProps {
  dataset: TimeSeriesDataset | undefined;
  entities: EntityMetadata[] | undefined;
}

function CompactView({ dataset, onClick }: CompactViewProps) {
  if (!dataset) return null;

  return (
    <div 
      onClick={onClick}
      className="bg-[#050a14] rounded-lg p-3 border-2 border-[#101827] hover:border-[#2a4170] hover:bg-[#0a101c] transition-all duration-200 cursor-pointer w-[280px] min-h-[180px] flex flex-col"
    >
      <div>
        <div className="flex justify-between items-start">
          <h3 className="text-sm font-medium text-white line-clamp-2 pr-2">{dataset.name}</h3>
          <div className="text-xs text-zinc-500 shrink-0">
            {format(new Date(dataset.updatedAt), 'MMM d')}
          </div>
        </div>
        <p className="text-xs text-zinc-400 mt-1">{dataset.description}</p>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-2">
        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Database size={14} className="text-blue-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Series</div>
            <div className="text-zinc-300 font-medium">{dataset.numSeries}</div>
          </div>
        </div>
        
        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <BarChart2 size={14} className="text-purple-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Features</div>
            <div className="text-zinc-300 font-medium">{dataset.numFeatures}</div>
          </div>
        </div>

        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Clock size={14} className="text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Timestamps</div>
            <div className="text-zinc-300 font-medium">{dataset.avgNumTimestamps.toFixed(0)}</div>
          </div>
        </div>

        <div className="flex items-start gap-1.5 p-2 rounded bg-[#0a101c]">
          <Layers size={14} className="text-emerald-400 mt-0.5 shrink-0" />
          <div className="text-xs min-w-0">
            <div className="text-zinc-500">Index</div>
            <div className="text-zinc-300 font-medium line-clamp-2">
              {dataset.indexFirstLevel}
              {dataset.indexSecondLevel && `, ${dataset.indexSecondLevel}`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FullView({ dataset, entities, onClose }: FullViewProps) {
  const [showDescription, setShowDescription] = useState(false);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [navigationHistory, setNavigationHistory] = useState<string[]>([]);

  if (!dataset) return null;

  const selectedEntity = entities?.find(e => e.entityId === selectedEntityId);

  const handleEntitySelect = (entityId: string) => {
    setSelectedEntityId(entityId);
    setNavigationHistory(prev => [...prev, entityId]);
  };

  const handleBack = () => {
    if (navigationHistory.length > 0) {
      const newHistory = [...navigationHistory];
      newHistory.pop();
      const previousEntityId = newHistory[newHistory.length - 1] || null;
      setSelectedEntityId(previousEntityId);
      setNavigationHistory(newHistory);
    }
  };

  return (
    <div className="bg-[#050a14] rounded-lg p-3 border-2 border-[#101827] w-full h-[600px] flex flex-col overflow-hidden">
      {/* Title always visible */}
      <div className="flex items-center gap-2 mb-2">
        <button
          onClick={handleBack}
          disabled={navigationHistory.length === 0}
          className={`text-zinc-400 transition-colors ${navigationHistory.length === 0 ? 'opacity-50' : 'hover:text-zinc-300'}`}
          title={navigationHistory.length === 0 ? "No history" : "Go back"}
        >
          <ArrowLeft size={18} />
        </button>
        <h2 className="text-lg font-semibold text-white">{dataset.name}</h2>
        <button
          onClick={() => setShowDescription(!showDescription)}
          className="text-zinc-400 hover:text-zinc-300 transition-colors"
          title={showDescription ? "Hide description" : "Show description"}
        >
          <Info size={16} />
        </button>
        <div className="flex-1" />
        <div className="text-sm text-zinc-500">
          Updated {format(new Date(dataset.updatedAt), 'MMM d, yyyy')}
        </div>
        <button
          onClick={onClose}
          className="text-zinc-400 hover:text-zinc-300 transition-colors ml-2"
          title="Close visualization"
        >
          <X size={16} />
        </button>
      </div>
      {showDescription && (
        <p className="text-sm text-zinc-400 mb-2">{dataset.description}</p>
      )}
      {/* Show dataset metadata card ONLY when no entity is selected (i.e., chart not toggled) */}
      {!selectedEntityId && (
        <div className="bg-[#0a101c] rounded-lg p-4 mb-4 border border-[#1a2234] shadow-sm flex flex-col gap-2">
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Database size={16} className="text-blue-400" />
              <div>
                <div className="text-xs text-zinc-500">Series</div>
                <div className="text-sm text-zinc-300 font-medium">{dataset.numSeries}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <BarChart2 size={16} className="text-purple-400" />
              <div>
                <div className="text-xs text-zinc-500">Features</div>
                <div className="text-sm text-zinc-300 font-medium">{dataset.numFeatures}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-amber-400" />
              <div>
                <div className="text-xs text-zinc-500">Avg. Timestamps</div>
                <div className="text-sm text-zinc-300 font-medium">{dataset.avgNumTimestamps.toFixed(0)}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-emerald-400" />
              <div>
                <div className="text-xs text-zinc-500">Index</div>
                <div className="text-sm text-zinc-300 font-medium">
                  {dataset.indexFirstLevel}
                  {dataset.indexSecondLevel && `, ${dataset.indexSecondLevel}`}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Main Content */}
      <div className="flex-1 min-h-0">
        {selectedEntityId && selectedEntity ? (
          <TimeSeriesEChart 
            entityId={selectedEntityId}
            entity={selectedEntity}
          />
        ) : (
          <div className="h-full bg-[#0a101c] rounded-lg overflow-hidden">
            <div className="h-full flex flex-col">
              {/* List Content */}
              <div className="flex-1 overflow-y-auto space-y-4">
                {entities?.map((entity) => (
                  <button
                    key={entity.entityId}
                    onClick={() => handleEntitySelect(entity.entityId)}
                    className="w-full text-left bg-[#101827] rounded-xl shadow-sm px-6 py-4 border border-[#1a2234] hover:bg-[#18213a] hover:scale-[1.002] transition-all group cursor-pointer flex flex-col gap-2"
                    style={{ boxShadow: '0 2px 8px 0 rgba(10,16,28,0.10)' }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <LineChart size={18} className="text-blue-400 shrink-0" />
                      <span className="text-sm bg-blue-900/40 px-4 py-1.5 rounded-full">
                        <span className="text-blue-100">Time Series </span>
                        <span className="text-white font-semibold">{entity.originalId}</span>
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-8 gap-y-1">
                      {entity.columnNames.map((name, index) => (
                        <div key={name} className="flex items-center gap-2 min-w-0">
                          <span className="text-xs text-zinc-500 min-w-[90px] truncate">{name}</span>
                          <span className="text-xs text-zinc-300 font-medium truncate">{entity.values[index]?.toString() || 'N/A'}</span>
                        </div>
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function TimeSeriesVisualizer(props: TimeSeriesVisualizerProps) {
  const { dataset, entities } = useTimeSeriesDataset(props.datasetId);
  return props.mode === "compact" ? <CompactView {...props} dataset={dataset} /> : <FullView {...props} dataset={dataset} entities={entities} />;
}

