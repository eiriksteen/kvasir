import { BarChart, X } from 'lucide-react';
import { getEntityMiniClasses } from '@/lib/entityColors';

interface AnalysisMiniProps {
  name: string;
  size?: 'sm' | 'md';
  onRemove?: () => void;
}

export function AnalysisMini({ name, size = 'md', onRemove }: AnalysisMiniProps) {
  const iconSize = size === 'sm' ? 10 : 12;
  const textSize = size === 'sm' ? 'text-xs' : 'text-xs';
  const padding = size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1';
  const colors = getEntityMiniClasses('analysis');

  return (
    <div className={`${padding} ${textSize} rounded-full flex items-center gap-1 ${colors.bg} ${colors.text}`}>
      <BarChart size={iconSize} />
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

