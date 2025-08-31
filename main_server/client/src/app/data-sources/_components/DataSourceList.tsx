import { DataSource } from "@/types/data-sources";
import FileInfoModal from "@/components/info-modals/FileInfoModal";
import { useState } from "react";
import SourceTypeIcon from "@/app/data-sources/_components/SourceTypeIcon";

function DataSourceListItem({ dataSource, isFirst }: { dataSource: DataSource; isFirst: boolean }) {

  return (
    <div className={`group flex items-center gap-2 p-2 bg-gray-900/50 border-b border-gray-800 hover:bg-gray-800/50 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t' : ''}`}>
      {SourceTypeIcon(dataSource.type, 16)}
      <div className="flex items-center gap-3 min-w-0">
        <h3 className="text-sm font-medium text-gray-200 truncate">
          {dataSource.name}
        </h3>
        <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-1 rounded flex-shrink-0">
          {dataSource.type}
        </span>
      </div>
    </div>
  );
}


export default function DataSourceList({ dataSources, isLoading, error }: { dataSources: DataSource[], isLoading: boolean, error: Error | null }) {
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);

  return (  
    <div>
        <div className="p-2">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">Added Data Sources</h3>
            <p className="text-sm text-gray-500 mt-1">
                You can use these sources inside projects and derive datasets, models, and functions from them.
            </p>
        </div>
        {!isLoading && !error && dataSources && dataSources.length > 0 ? (
            <div className="grid gap-0 max-h-[70vh] overflow-y-auto">
            {dataSources.map((dataSource, index) => (
                <div key={dataSource.id} onClick={() => setSelectedDataSource(dataSource)}>
                    <DataSourceListItem dataSource={dataSource} isFirst={index === 0} />
                </div>
            ))}
            </div>
        ) : (
            <div className="flex items-center justify-center pt-10 py-30">
                <div className="text-gray-400">No data sources yet</div>
            </div>
        )}
        {selectedDataSource && <FileInfoModal dataSourceId={selectedDataSource.id} onClose={() => setSelectedDataSource(null)} />}
    </div>
  );
}