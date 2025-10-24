'use client';

import { useState, useMemo, useEffect, useRef } from 'react';
import { X, Database } from 'lucide-react';
import { useDataSources, useProjectDataSources } from '@/hooks/useDataSources';
import { useProject } from '@/hooks/useProject';
import { DataSource } from '@/types/data-sources';
import SourceTypeIcon from "@/app/data-sources/_components/SourceTypeIcon";
import { UUID } from 'crypto';

function DataSourceListItem({ dataSource, isFirst }: { dataSource: DataSource; isFirst: boolean }) {

  return (
    <div className={`group flex items-center gap-2 p-2 bg-gray-50 border-b border-gray-200 hover:bg-gray-100 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t border-gray-200' : ''}`}>
      {SourceTypeIcon(dataSource.type, 16)}
      <div className="flex items-center gap-3 min-w-0">
        <h3 className="text-sm font-medium text-gray-900 truncate">
          {dataSource.name}
        </h3>
        <span className="text-xs font-mono text-gray-600 bg-gray-200 px-2 py-1 rounded flex-shrink-0">
          {dataSource.type}
        </span>
      </div>
    </div>
  );
}

interface AddDataSourceProps {
  onClose: () => void;
  projectId: UUID;
}

export default function AddDataSource({ onClose, projectId }: AddDataSourceProps) {
  // Need all data sources to display options to add
  const { dataSources, isLoading, error } = useDataSources();
  // Need just mutate the project data sources to update the ERD
  const { mutateDataSources: mutateProjectDataSources } = useProjectDataSources(projectId);
  const { project, addEntity } = useProject(projectId);
  const [isAdding, setIsAdding] = useState<string | null>(null);
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

  // Filter out data sources that are already in the project
  const availableDataSources = useMemo(() => {
    if (!project || !dataSources) return [];
    const projectDataSourceIds = project.dataSources.map(ds => ds.dataSourceId);
    return dataSources.filter(dataSource => 
      !projectDataSourceIds.includes(dataSource.id)
    );
  }, [project, dataSources]);

  const handleAddDataSource = async (dataSource: DataSource) => {
    if (!project || isAdding === dataSource.id) return;
    
    setIsAdding(dataSource.id);
    try {
      await addEntity("data_source", dataSource.id);
      // Close the modal after successful addition
      onClose();
    } catch (error) {
      console.error('Failed to add data source to project:', error);
    } finally {
      setIsAdding(null);
      await mutateProjectDataSources();
    }
  };

  return (
    <div ref={backdropRef} className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-gray-300 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full">
          <div className="p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600">Add Data Source</h3>
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
                <div className="text-center text-gray-500">
                  <Database size={48} className="mx-auto mb-4 opacity-50"/>
                  <p className="font-medium text-gray-600 text-lg">No data sources available</p>
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