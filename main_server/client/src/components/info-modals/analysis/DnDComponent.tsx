import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { UUID } from 'crypto';

interface DnDComponentProps {
  nextType: 'analysis_result' | 'notebook_section' | null;
  nextId: UUID | null;
  sectionId: UUID | null;
}

const DnDComponent: React.FC<DnDComponentProps> = ({
  nextType,
  nextId,
  sectionId
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: `dnd-${sectionId}-${nextType}-${nextId}`,
    data: {
      nextType,
      nextId,
      sectionId,
      type: 'dnd-zone'
    }
  });

  return (
    <div
      ref={setNodeRef}
      className={`w-full transition-all duration-200 ${
        isOver
          ? 'h-8 bg-purple-500/20 border-2 border-purple-400 border-dashed rounded'
          : 'h-1 bg-transparent'
      }`}
    >
      {isOver ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-xs text-purple-300 font-medium">
            Drop here to reorder
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default DnDComponent;