'use client';

import { useEffect, useState } from 'react';
import { X, Folder } from 'lucide-react';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';
import { useProjectDataSources } from '@/hooks/useDataSources';
import { useProjectChat } from '@/hooks/useProjectChat';
import { DataSource } from '@/types/data-sources';
import SourceTypeIcon from "@/app/data-sources/_components/SourceTypeIcon";

function DataSourceListItem({ dataSource, isFirst, isInContext }: { dataSource: DataSource; isFirst: boolean; isInContext: boolean }) {
  return (
    <div className={`group flex items-center gap-2 p-2 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t' : ''} ${
      isInContext 
        ? 'bg-emerald-500/10 border-b border-emerald-500/20' 
        : 'bg-gray-900/50 border-b border-gray-800 hover:bg-gray-800/50'
    }`}>
      {SourceTypeIcon(dataSource.type, 16)}
      <div className="flex items-center gap-3 min-w-0">
        <h3 className="text-sm font-medium text-gray-200 truncate">
          {dataSource.name}
        </h3>
        <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-1 rounded flex-shrink-0">
          {dataSource.type}
        </span>
      </div>
      {isInContext && (
        <span className="text-xs text-emerald-400 font-mono ml-auto">✓</span>
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

  const { dataSources } = useProjectDataSources(projectId);
  const { 
    dataSourcesInContext, 
    addDataSourceToContext, 
    removeDataSourceFromContext 
  } = useAgentContext(projectId);

  const { submitPrompt } = useProjectChat(projectId);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const handleDataSourceToggle = (dataSource: DataSource) => {
    const isActive = dataSourcesInContext.some((d: DataSource) => d.id === dataSource.id);
    if (isActive) {
      removeDataSourceFromContext(dataSource);
    } else {
      addDataSourceToContext(dataSource);
    }
  };

  const handleSubmit = async () => {
    await submitPrompt(`Create a new dataset from the data sources in the context!${description ? `\n\nDescription: ${description}` : ''}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-6">Add Dataset</h3>
          
          {/* Data Sources */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-200">Data Sources</h4>
              <span className="text-xs text-gray-500">
                {dataSourcesInContext.length} in context
              </span>
            </div>
            
            <div className="overflow-y-auto max-h-[40vh]">
              {dataSources && dataSources.length > 0 ? (
                <div className="grid gap-0">
                  {dataSources.map((dataSource: DataSource, index: number) => {
                    const isInContext = dataSourcesInContext.some((d: DataSource) => d.id === dataSource.id);
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
            <label htmlFor="description" className="block text-sm font-medium text-gray-200 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional: The target dataset description. If none provided, the agent will make its own assumptions."
              className="w-full h-full p-2 bg-gray-900/50 border border-gray-800 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 resize-none text-sm"
            />
          </div>

          {/* Submit Button */}
          <div className="mt-auto border-gray-800">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || dataSourcesInContext.length === 0}
              className="w-full h-10 flex items-center justify-center gap-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
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