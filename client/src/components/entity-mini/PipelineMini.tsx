import { Zap, X } from 'lucide-react';

interface PipelineMiniProps {
  name: string;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export function PipelineMini({ name, size = 'md', onRemove }: PipelineMiniProps) {
  const iconSize = size === 'sm' ? 10 : 12;
  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';

  return (
    <div className={`${padding} ${textSize} rounded-full flex items-center gap-1 bg-[#840B08]/20 text-[#840B08]`}>
      <Zap size={iconSize} />
      <span className="truncate">{name}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="text-[#840B08] hover:text-gray-400 flex-shrink-0"
        >
          <X size={iconSize} />
        </button>
      )}
    </div>
  );
}

