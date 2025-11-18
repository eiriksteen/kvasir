import React, { useState, useEffect, useRef } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { Section, AnalysisCell } from '@/types/ontology/analysis';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import DnDComponent from '@/components/info-tabs/analysis/DnDComponent';
import { useAnalysis } from '@/hooks/useAnalysis';
import { Trash2, Move, MoreVertical, Pencil, Save, Loader2, X } from 'lucide-react';
import { UUID } from 'crypto';
import CellItem from '@/components/info-tabs/analysis/CellItem';

interface SectionItemProps {
  section: Section;
  sections: Section[];
  projectId: UUID;
  analysisObjectId: UUID;
  depth?: number;
  numbering: string;
  onScrollToSection?: (sectionId: string) => void;
  setSectionRef?: (sectionId: string) => (element: HTMLDivElement | null) => void;
  expandedSections?: Set<string>;
  setExpandedSections?: React.Dispatch<React.SetStateAction<Set<string>>>;
}


const SectionItem: React.FC<SectionItemProps> = ({ 
  section, 
  projectId, 
  analysisObjectId,
  numbering,
  expandedSections: parentExpandedSections,
  setExpandedSections: parentSetExpandedSections
}) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [showEditSection, setShowEditSection] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [editName, setEditName] = useState(section.name);
  const [editDescription, setEditDescription] = useState(section.description || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  
  // Check if this section should be expanded based on parent state
  const isExpanded = parentExpandedSections?.has(section.id) || false;
  
  const {
    mutateAnalysis,
  } = useAnalysis(analysisObjectId);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu]);

  // Focus name input when editing starts
  useEffect(() => {
    if (showEditSection && nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, [showEditSection]);

  // Drag functionality for sections
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: section.id,
    data: {
      type: 'notebook_section',
      section: section
    }
  });



  const handleDeleteSection = async (sectionId: UUID) => {
    // TODO: Implement delete section API call
    // For now, just close the confirmation
    setShowConfirm(false);
    console.log('Delete section:', sectionId);
  };

  const handleUpdateSection = async () => {
    if (editName.trim() && !isUpdating) {
      setIsUpdating(true);
      try {
        // TODO: Implement update section API call
        // For now, just update local state
        await mutateAnalysis();
        setShowEditSection(false);
      } catch (error) {
        console.error('Error updating section:', error);
      } finally {
        setIsUpdating(false);
      }
    }
  };

  const handleCancelEdit = () => {
    setEditName(section.name);
    setEditDescription(section.description || '');
    setShowEditSection(false);
  };

  // Helper function to determine title size based on numbering depth
  const getTitleStyle = (numbering: string) => {
    const depth = numbering.split('.').length;
    switch (depth) {
      case 1: return 'text-base font-mono';
      case 2: return 'text-base font-mono';
      case 3: return 'text-lg font-semibold';
      default: return 'text-lg font-semibold';
    }
  };

  // Get cells ordered by their order field
  const orderedCells = section.cells 
    ? [...section.cells].sort((a, b) => a.order - b.order)
    : [];

  return (
    <div className="w-full">
      {/* DnD Component - positioned above the section header, only when not dragging */}
      {!isDragging && (
        <DnDComponent
          nextType={"notebook_section"}
          nextId={section.id}
          sectionId={null}
        />
      )}
      
      {/* Section Header */}
      <div 
        ref={setNodeRef}
        className={`flex items-center gap-2 py-2 transition-colors ${
          isDragging ? 'opacity-50' : 'opacity-100'
        }`}
        style={transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` } : {}}
      >
        {isDragging ? (
          <div className="w-full h-8 bg-[#0E4F70]/20 flex items-center justify-center rounded-lg">
            <div className="flex items-center gap-2">
              <Move size={16} className="text-[#0E4F70] animate-pulse" />
              <span className="text-sm text-[#0E4F70]">Moving section...</span>
            </div>
          </div>
        ) : (
          <div className="w-full">
            <div 
              className="flex items-center gap-2 w-full cursor-pointer" 
              onClick={() => {
                if (!showEditSection && parentSetExpandedSections) {
                  parentSetExpandedSections(prev => {
                    const newSet = new Set(prev);
                    if (newSet.has(section.id)) {
                      newSet.delete(section.id);
                    } else {
                      newSet.add(section.id);
                    }
                    return newSet;
                  });
                }
              }}
            >
              {showEditSection ? (
                <div className="flex-1 space-y-2">
                  <input
                    ref={nameInputRef}
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className={`w-full ${getTitleStyle(numbering)} px-2 py-1 rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]`}
                    placeholder="Section name..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleUpdateSection();
                      if (e.key === 'Escape') handleCancelEdit();
                    }}
                    disabled={isUpdating}
                  />
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="w-full text-xs px-2 py-1 rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70] resize-none"
                    placeholder="Section description (optional)..."
                    rows={2}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') handleCancelEdit();
                    }}
                    disabled={isUpdating}
                  />
                  <div className="flex items-center justify-evenly gap-2">
                    <button
                      onClick={handleCancelEdit}
                      disabled={isUpdating}
                      className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <X size={16} />
                      <span>Cancel</span>
                    </button>
                    <button
                      onClick={handleUpdateSection}
                      disabled={isUpdating || !editName.trim()}
                      className="flex-1 p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                      <span>{isUpdating ? 'Saving...' : 'Save'}</span>
                    </button>
                  </div>
                </div>
              ) : (
                <span className={`${getTitleStyle(numbering)} text-gray-900 flex-1`}>
                  {numbering}. {section.name}
                </span>
              )}
              
              {/* Vertical ellipsis menu - only show when not editing */}
              {!showEditSection && (
                <div className="relative" ref={menuRef}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(!showMenu);
                    }}
                    className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                    title="More options"
                  >
                    <MoreVertical size={14} />
                  </button>
                
                {showMenu && (
                  <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-300 rounded-lg shadow-xl z-50">
                    <div className="py-1">
                      <div {...listeners} {...attributes}>
                        <button
                          className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                          onClick={() => setShowMenu(false)}
                        >
                          <Move size={14} />
                          Move section
                        </button>
                      </div>
                      <button
                        onClick={() => {
                          setShowEditSection(true);
                          setShowMenu(false);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center gap-2"
                      >
                        <Pencil size={14} />
                        Edit section
                      </button>
                      <button
                        onClick={() => {
                          setShowConfirm(true);
                          setShowMenu(false);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-gray-100 flex items-center gap-2"
                      >
                        <Trash2 size={14} />
                        Delete section
                      </button>
                    </div>
                  </div>
                )}
                </div>
              )}
            </div>
            {/* Expandable Content */}
            {isExpanded && (
              <div>
                {/* Section Description */}
                {section.description && !showEditSection && (
                  <div className="text-sm text-gray-700 mb-2 leading-relaxed">
                    {section.description}
                  </div>
                )}
                
                {/* Ordered Cells */}
                {orderedCells.length > 0 && (
                  <div>
                    {orderedCells.map((cell: AnalysisCell) => (
                      <CellItem
                        key={cell.id}
                        cell={cell}
                        projectId={projectId}
                        analysisObjectId={analysisObjectId}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
      {/* Edit Mode Actions */}
      

      {!isDragging && (
        <DnDComponent
          nextType={null}
          nextId={null}
          sectionId={section.id}
        />
      )}

      <ConfirmationPopup
        message="Are you sure you want to delete this section and all its subsections?"
        isOpen={showConfirm}
        onConfirm={() => handleDeleteSection(section.id)}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  );
};

export default SectionItem; 