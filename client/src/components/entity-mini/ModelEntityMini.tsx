import { Brain, X } from 'lucide-react';
import { getEntityMiniClasses } from '@/lib/entityColors';

interface ModelEntityMiniProps {
  name: string;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export function ModelEntityMini({ name, size = 'md', onRemove }: ModelEntityMiniProps) {
  const iconSize = size === 'sm' ? 10 : 12;
  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';
  const colors = getEntityMiniClasses('model_instantiated');

  return (
    <div className={`${padding} ${textSize} rounded-full flex items-center gap-1 ${colors.bg} ${colors.text}`}>
      <Brain size={iconSize} />
      <span className="truncate">{name}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className={`${colors.text} ${colors.hover} flex-shrink-0`}
        >
          <X size={iconSize} />
        </button>
      )}
    </div>
  );
}

