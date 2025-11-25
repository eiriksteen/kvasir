'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Folder } from 'lucide-react';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';
import { useOntology } from '@/hooks/useOntology';
import { useKvasirV1 } from '@/hooks/useKvasirV1';
import { DataSource } from '@/types/ontology/data-source';
import { DatasetCreate } from '@/types/ontology/dataset';

function DataSourceListItem({ dataSource, isFirst, isInContext }: { dataSource: DataSource; isFirst: boolean; isInContext: boolean }) {
  return (
    <div className={`group flex items-center gap-2 p-2 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t border-gray-200' : ''} ${
      isInContext
        ? 'bg-gray-100 border-b border-gray-300'
        : 'bg-gray-50 border-b border-gray-200 hover:bg-gray-100'
    }`}>
      <div className="flex items-center gap-3 min-w-0">
        <h3 className="text-sm font-medium text-gray-900 truncate">
          {dataSource.name}
        </h3>
        <span className="text-xs font-mono text-gray-600 bg-gray-200 px-2 py-1 rounded flex-shrink-0">
          {dataSource.type}
        </span>
      </div>
      {isInContext && (
        <span className="text-xs text-gray-700 font-mono ml-auto">✓</span>
      )}
    </div>
  );
}

interface AddDatasetProps {
  onClose: () => void;
  projectId: UUID;
}

export default function AddDataset({ onClose, projectId }: AddDatasetProps) {
  const [description, setDescription] = useState('');
  const [isSubmitting] = useState(false);

  const { dataSources, insertDataset, mutateEntityGraph } = useOntology(projectId);

  const { 
    dataSourcesInContext, 
    addDataSourceToContext, 
    removeDataSourceFromContext 
  } = useAgentContext(projectId);

  const { submitPrompt } = useKvasirV1(projectId);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (backdropRef.current && event.target === backdropRef.current) {
        onClose();
      }
    };

    const backdrop = backdropRef.current;
    if (backdrop) {
      backdrop.addEventListener('click', handleClickOutside);
      return () => backdrop.removeEventListener('click', handleClickOutside);
    }
  }, [onClose]);

  const handleDataSourceToggle = (dataSource: DataSource) => {
    const isActive = dataSourcesInContext.some((d: UUID) => d === dataSource.id);
    if (isActive) {
      removeDataSourceFromContext(dataSource.id);
    } else {
      addDataSourceToContext(dataSource.id);
    }
  };

  const handleSubmit = async () => {
    try {
      const datasetCreate: DatasetCreate = {
        name: 'New Dataset',
        description: description || '',
        groups: []
      };
      const newDataset = await insertDataset({ datasetCreate: datasetCreate, edges: [] });
      await submitPrompt(`Populate the dataset ${newDataset.name} from the data sources in the context!${description ? `\n\nDescription: ${description}` : ''}`);
      onClose();
    } finally {
      await mutateEntityGraph();
    }
  };

  return (
    <div ref={backdropRef} className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-[#0E4F70]/20 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600 mb-6">Add Dataset</h3>
          
          {/* Data Sources */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-900">Data Sources</h4>
              <span className="text-xs text-gray-500">
                {dataSourcesInContext.length} in context
              </span>
            </div>
            
            <div className="overflow-y-auto max-h-[40vh]">
              {dataSources && dataSources.length > 0 ? (
                <div className="grid gap-0">
                  {dataSources.map((dataSource: DataSource, index: number) => {
                    const isInContext = dataSourcesInContext.some((d: UUID) => d === dataSource.id);
                    return (
                      <div key={dataSource.id} onClick={() => handleDataSourceToggle(dataSource)}>
                        <DataSourceListItem 
                          dataSource={dataSource} 
                          isFirst={index === 0}
                          isInContext={isInContext}
                        />
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <p className="text-sm">No data sources available</p>
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">Click to add/remove from context</p>
          </div>

          {/* Dataset Description */}
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-900 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional: The target dataset description. If none provided, the agent will make its own assumptions."
              className="w-full h-full p-2 bg-gray-50 border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#000034]/50 focus:border-[#000034]/50 transition-all duration-200 resize-none text-sm"
            />
          </div>

          {/* Submit Button */}
          <div className="mt-auto border-t border-gray-200">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || dataSourcesInContext.length === 0}
              className="w-full h-10 flex items-center justify-center gap-2 px-4 bg-[#000034] hover:bg-[#000044] disabled:bg-gray-300 disabled:text-gray-500 text-white font-medium rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
            >
              <Folder size={16} />
              {isSubmitting ? 'Creating Dataset...' : 'Create Dataset'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 