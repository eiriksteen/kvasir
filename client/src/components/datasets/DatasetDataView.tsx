import { EntityMetadata } from '@/types/datasets';
import { LineChart } from 'lucide-react';

interface DatasetDataViewProps {
  entities: EntityMetadata[] | undefined;
  onEntitySelect: (entityId: string) => void;
}

export default function DatasetDataView({ entities, onEntitySelect }: DatasetDataViewProps) {
  return (
    <div className="h-full bg-[#0a101c] rounded-lg overflow-hidden">
      <div className="h-full flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 p-2">
          {entities?.map((entity) => (
            <button
              key={entity.entityId}
              onClick={() => onEntitySelect(entity.entityId)}
              className="w-full text-left bg-[#101827] rounded-xl shadow-sm px-6 py-4 border border-[#1a2234] hover:bg-[#18213a] hover:scale-[1.002] transition-all group cursor-pointer flex flex-col gap-2"
              style={{ boxShadow: '0 2px 8px 0 rgba(10,16,28,0.10)' }}
            >
              <div className="flex items-center gap-3 mb-2">
                <LineChart size={18} className="text-blue-400 shrink-0" />
                <span className="text-xs font-mono bg-blue-900/40 px-4 py-1.5 rounded-full">
                  <span className="text-blue-100">Time Series </span>
                  <span className="text-white font-mono">{entity.originalId}</span>
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-1">
                {entity.columnNames.map((name, index) => (
                  <div key={name} className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-mono text-gray-500 min-w-[90px] truncate">{name}</span>
                    <span className="text-xs font-mono text-gray-200 truncate">{entity.values[index]?.toString() || 'N/A'}</span>
                  </div>
                ))}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
} 