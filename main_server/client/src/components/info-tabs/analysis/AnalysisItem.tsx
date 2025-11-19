import React, { useRef, useCallback, useState, useEffect } from 'react';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import SectionItem from '@/components/info-tabs/analysis/SectionItem';
import TableOfContents from '@/components/info-tabs/analysis/TableOfContents';
import { Bot } from 'lucide-react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { UUID } from 'crypto';

interface AnalysisItemProps {
  analysisObjectId: UUID;
  projectId: UUID;
  onClose?: () => void;
}


const AnalysisItem: React.FC<AnalysisItemProps> = ({
  analysisObjectId,
  projectId,
  onClose,
}) => {
  const {
    analysis,
  } = useAnalysis(projectId, analysisObjectId);
  
  // Refs for scrolling to sections
  const sectionRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  
  // Expansion state for sections in main content - initially expand all sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  // Update expanded sections when analysis loads
  useEffect(() => {
    if (analysis?.sections) {
      const allSectionIds = new Set<string>();
      analysis.sections.forEach(section => {
        allSectionIds.add(section.id);
      });
      setExpandedSections(allSectionIds);
    }
  }, [analysis]);
  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [onClose]);

  // Function to scroll to a specific section
  const scrollToSection = useCallback((sectionId: string) => {
    const element = sectionRefs.current.get(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start',
        inline: 'nearest'
      });
    }
  }, []);


  // Enhanced scroll handler that also handles expansion
  const handleScrollToSection = useCallback((sectionId: string) => {
    if (!analysis?.sections) return;
    
    // Expand the section in main content
    setExpandedSections((prev: Set<string>) => {
      const newSet = new Set(prev);
      newSet.add(sectionId);
      return newSet;
    });
    
    // Wait a bit for the expansion to render, then scroll
    setTimeout(() => {
      scrollToSection(sectionId);
    }, 100);
  }, [scrollToSection, analysis]);

  // Function to set ref for a section
  const setSectionRef = useCallback((sectionId: string) => (element: HTMLDivElement | null) => {
    if (element) {
      sectionRefs.current.set(sectionId, element);
    } else {
      sectionRefs.current.delete(sectionId);
    }
  }, []);

  // Handle drag end event for the new DnD system
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (!over) return;
    
    // TODO: Implement drag and drop for new structure
    // The new structure uses cells within sections, so DnD logic needs to be updated
    console.log('Drag end:', { active, over });
  };

  if (!analysis) {
    return (
      <div className="w-full h-full bg-white overflow-hidden">
        <div className="bg-white h-full px-0 pb-2 relative">
          <div className="flex flex-col h-full">
            <div className="flex-1 min-h-0">
              <div className="h-full p-4">
                <div className="text-center py-8">
                  <Bot size={48} className="mx-auto text-gray-600 mb-4" />
                  <p className="text-gray-500">Loading analysis...</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Get sections ordered by their order field (or by creation if no order)
  const orderedSections = analysis?.sections 
    ? [...analysis.sections].sort((a, b) => {
        // Sort by order if available, otherwise by creation date
        return (a.createdAt < b.createdAt ? -1 : 1);
      })
    : [];

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full relative">
        <div className="flex flex-col h-full">
          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full">
              <DndContext onDragEnd={handleDragEnd}>
                <div className="flex h-full">
                  {/* Table of Contents - Left Side - Responsive */}
                  <div className="flex-shrink-0 sticky h-full overflow-y-auto">
                    <TableOfContents
                      analysisObjectId={analysisObjectId}
                      projectId={projectId}
                      onScrollToSection={handleScrollToSection}
                    />
                  </div>
                  {/* Main Content - Right Side */}
                  <div className="flex-1 text-sm text-gray-600 flex flex-col overflow-y-auto">
                    {/* Sections Content */}
                    {orderedSections.length > 0 && (
                      <div className="flex-1 px-2">
                        {orderedSections.map((section, index) => (
                          <div key={section.id} ref={setSectionRef(section.id)}>
                            <SectionItem
                              section={section}
                              sections={orderedSections}
                              projectId={projectId}
                              analysisObjectId={analysisObjectId}
                              depth={0}
                              numbering={`${index + 1}`}
                              onScrollToSection={handleScrollToSection}
                              setSectionRef={setSectionRef}
                              expandedSections={expandedSections}
                              setExpandedSections={setExpandedSections}
                            />
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Empty State */}
                    {orderedSections.length === 0 && (
                      <div className="flex-1 text-center py-8">
                        <Bot size={48} className="mx-auto text-gray-600 mb-4" />
                        <p className="text-gray-500 mb-4">No sections created yet.</p>
                      </div>
                    )}
                  </div>
                </div>
              </DndContext>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisItem; 