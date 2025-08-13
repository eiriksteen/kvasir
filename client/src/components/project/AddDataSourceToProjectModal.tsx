'use client';

import { useState, useEffect, useMemo } from 'react';
import { X, Database } from 'lucide-react';
import { useDataSources } from '@/hooks/useDataSources';
import { useProject } from '@/hooks/useProject';
import { DataSource } from '@/types/data-sources';
import DataSourceListItem from '@/components/data-sources/DataSourceListItem';

interface AddDataSourceToProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export default function AddDataSourceToProjectModal({ isOpen, onClose, projectId }: AddDataSourceToProjectModalProps) {
  const { dataSources, mutateDataSources, isLoading, error } = useDataSources();
  const { selectedProject, addEntity } = useProject(projectId);
  const [isAdding, setIsAdding] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setIsAdding(null);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    } else {
      window.removeEventListener('keydown', handleKeyDown);
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Filter out data sources that are already in the project
  const availableDataSources = useMemo(() => {
    if (!selectedProject || !dataSources) return [];
    return dataSources.filter(dataSource => 
      !selectedProject.dataSourceIds.includes(dataSource.id)
    );
  }, [selectedProject, dataSources]);

  const handleAddDataSource = async (dataSource: DataSource) => {
    if (!selectedProject || isAdding === dataSource.id) return;
    
    setIsAdding(dataSource.id);
    try {
      await addEntity("data_source", dataSource.id);
      await mutateDataSources();
      // Close the modal after successful addition
      onClose();
    } catch (error) {
      console.error('Failed to add data source to project:', error);
    } finally {
      setIsAdding(null);
    }
  };

  if (!isOpen) return null;

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

        <div className="flex flex-col h-full">
          <div className="p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">Add Data Sources</h3>
          </div>

          <div className="flex-grow overflow-y-auto">
            {!isLoading && !error && availableDataSources && availableDataSources.length > 0 ? (
              <div className="grid gap-0">
                {availableDataSources.map((dataSource, index) => (
                  <div key={dataSource.id} onClick={() => handleAddDataSource(dataSource)}>
                    <DataSourceListItem 
                      key={dataSource.id} 
                      dataSource={dataSource} 
                      isFirst={index === 0}
                      />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center pt-10 py-30">
                <div className="text-center text-zinc-500">
                  <Database size={48} className="mx-auto mb-4 opacity-50"/>
                  <p className="font-medium text-zinc-400 text-lg">No data sources available</p>
                  <p className="text-sm mt-2">All your data sources are already in this project</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 