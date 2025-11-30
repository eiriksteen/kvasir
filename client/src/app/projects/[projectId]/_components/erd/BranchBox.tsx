import React from 'react';
import { Database, Folder, BarChart3, Zap, Brain, FolderTree } from 'lucide-react';
import { BranchNode, BranchType, EntityType } from '@/types/ontology/entity-graph';
import { getBranchColorClasses, getEntityBoxClasses } from '@/lib/entityColors';

interface BranchBoxProps {
  branchNode: BranchNode;
}

function formatBranchType(branchType: string): string {
  if (branchType === 'mixed') {
    return '';
  }
  return branchType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getEntityIcon(branchType: BranchType) {
  switch (branchType) {
    case 'data_source':
      return Database;
    case 'dataset':
      return Folder;
    case 'analysis':
      return BarChart3;
    case 'pipeline':
      return Zap;
    case 'model_instantiated':
      return Brain;
    case 'mixed':
      return FolderTree;
    default:
      return FolderTree;
  }
}

export default function BranchBox({ branchNode }: BranchBoxProps) {
  const handleClick = (event: React.MouseEvent) => {
    console.log('Branch node clicked:', branchNode);
    event.stopPropagation();
  };
  
  const branchColors = getBranchColorClasses(branchNode.branchType);
  const isMixed = branchNode.branchType === 'mixed';
  const entityColors = !isMixed ? getEntityBoxClasses(branchNode.branchType as EntityType) : null;
  const colors = isMixed ? branchColors : {
    ...branchColors,
    iconBg: entityColors!.iconBg,
    iconBorder: entityColors!.iconBorder,
    iconColor: entityColors!.iconColor,
    labelColor: entityColors!.labelColor,
  };
  const branchTypeLabel = formatBranchType(branchNode.branchType);
  const displayLabel = branchTypeLabel ? `${branchTypeLabel} Group` : 'Group';
  const IconComponent = getEntityIcon(branchNode.branchType);
  const childCount = branchNode.children?.length || 0;
  
  return (
    <div
      className={`px-3 py-3 shadow-md rounded-md relative min-w-[100px] max-w-[240px] cursor-pointer ${colors.hoverBg}`}
      onClick={handleClick}
    >
      <svg
        className="absolute inset-0 pointer-events-none rounded-md"
        style={{ width: '100%', height: '100%' }}
      >
        <rect
          x="1"
          y="1"
          width="calc(100% - 2px)"
          height="calc(100% - 2px)"
          rx="6"
          ry="6"
          fill="none"
          stroke={colors.stroke}
          strokeWidth="2"
          strokeDasharray="8 4"
        />
      </svg>
      <div className="flex flex-col relative z-10">
        <div className="flex items-center mb-2">
          {isMixed ? (
            <div className={`rounded-full w-6 h-6 flex items-center justify-center ${colors.iconBg} border ${colors.iconBorder} mr-2`}>
              <IconComponent className={`w-3 h-3 ${colors.iconColor}`} />
            </div>
          ) : (
            <div className={`rounded-full w-auto h-6 flex items-center gap-1.5 px-1.5 ${colors.iconBg} border ${colors.iconBorder} mr-2`}>
              <IconComponent className={`w-3 h-3 ${colors.iconColor}`} />
              <span className={`text-xs font-mono ${colors.iconColor}`}>
                {childCount}
              </span>
            </div>
          )}
          <div className={`${colors.labelColor} font-mono text-xs`}>{displayLabel}</div>
        </div>
        <div>
          <div className="text-xs font-mono text-gray-800 break-words">{branchNode.name}</div>
        </div>
      </div>
    </div>
  );
}
