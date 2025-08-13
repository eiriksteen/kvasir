import { DataSource } from "@/types/data-sources";
import FileInfoModal from "@/components/data-sources/FileInfoModal";
import { useState } from "react";
import DataSourceListItem from "@/components/data-sources/DataSourceListItem";


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
        {selectedDataSource && <FileInfoModal dataSource={selectedDataSource} setSelectedDataSource={setSelectedDataSource} />}
    </div>
  );
}