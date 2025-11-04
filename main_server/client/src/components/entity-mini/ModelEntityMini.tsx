import { Brain, X } from 'lucide-react';

interface ModelEntityMiniProps {
  name: string;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export function ModelEntityMini({ name, size = 'md', onRemove }: ModelEntityMiniProps) {
  const iconSize = size === 'sm' ? 10 : 12;
  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';

  return (
    <div className={`${padding} ${textSize} rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]`}>
      <Brain size={iconSize} />
      <span className="truncate">{name}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="text-[#491A32] hover:text-gray-400 flex-shrink-0"
        >
          <X size={iconSize} />
        </button>
      )}
    </div>
  );
}

