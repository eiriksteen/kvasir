import { Database, X } from 'lucide-react';

interface DataSourceMiniProps {
  name: string;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export function DataSourceMini({ name, size = 'md', onRemove }: DataSourceMiniProps) {
  const iconSize = size === 'sm' ? 10 : 12;
  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';

  return (
    <div className={`${padding} ${textSize} rounded-full flex items-center gap-1 bg-gray-200 text-gray-600`}>
      <Database size={iconSize} />
      <span className="truncate">{name}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="text-gray-600 hover:text-gray-400 flex-shrink-0"
        >
          <X size={iconSize} />
        </button>
      )}
    </div>
  );
}

