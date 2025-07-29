import { DataSource } from "@/types/data-integration";
import { getSourceTypeIcon } from "@/lib/data-sources/sourceTypes";

export default function DataSourceListItem({ dataSource, isFirst }: { dataSource: DataSource; isFirst: boolean }) {

  return (
    <div className={`group flex items-center gap-2 p-2 bg-gray-900/50 border-b border-gray-800 hover:bg-gray-800/50 transition-all duration-200 cursor-pointer ${isFirst ? 'border-t' : ''}`}>
      {getSourceTypeIcon(dataSource.type, 16)}
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