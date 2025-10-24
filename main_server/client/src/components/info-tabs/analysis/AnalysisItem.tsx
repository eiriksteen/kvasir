import React, { Fragment, useRef, useCallback, useState, useEffect } from 'react';
import { DndContext, DragEndEvent } from '@dnd-kit/core';
import SectionItem from '@/components/info-tabs/analysis/SectionItem';
import TableOfContents from '@/components/info-tabs/analysis/TableOfContents';
import AnalysisResult from '@/components/info-tabs/analysis/AnalysisResult';
import { Bot } from 'lucide-react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { buildOrderedList, findParentSections } from '@/lib/utils';
import { UUID } from 'crypto';
import { NotebookSection, AnalysisResult as AnalysisResultType, MoveRequest } from '@/types/analysis';

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
    currentAnalysisObject: analysis,
    moveElement,
  } = useAnalysis(projectId, analysisObjectId);
  
  // Refs for scrolling to sections
  const sectionRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  
  // Expansion state for sections in main content - initially expand all sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  // Update expanded sections when analysis loads
  useEffect(() => {
    if (analysis?.notebook?.notebookSections) {
      const allSectionIds = new Set<string>();
      const collectSectionIds = (sections: NotebookSection[]) => {
        sections.forEach(section => {
          allSectionIds.add(section.id);
          if (section.notebookSections) {
            collectSectionIds(section.notebookSections);
          }
        });
      };
      collectSectionIds(analysis.notebook.notebookSections);
      setExpandedSections(allSectionIds);
    }
  }, [analysis]);

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
    if (!analysis?.notebook?.notebookSections) return;
    
    // Find all parent sections that need to be expanded
    const parentIds = findParentSections(sectionId, analysis.notebook.notebookSections);
    
    // Expand all parent sections in main content
    const allParentIds = [...parentIds, sectionId];
    setExpandedSections((prev: Set<string>) => {
      const newSet = new Set(prev);
      allParentIds.forEach(id => newSet.add(id));
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
    
    // Handle the new DnD system
    if (over.data.current?.type === 'dnd-zone') {
      const draggedId = active.id as UUID;
      const draggedType = active.data.current?.type as 'analysis_result' | 'notebook_section';
      const { nextType, nextId, sectionId } = over.data.current;
      
      // Create MoveRequest
      const moveRequest: MoveRequest = {
        newSectionId: sectionId as UUID,
        movingElementType: draggedType,
        movingElementId: draggedId,
        nextElementType: nextType,
        nextElementId: nextId
      };
      // Call the moveElement function
      moveElement({
        analysisObjectId,
        moveRequest
      });
    }
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

  // Build ordered list using the new nextType/nextId system
  const allSections = analysis.notebook?.notebookSections || [];
  const allResults = allSections.flatMap(section => section.analysisResults || []);
  
  // Find the first element in the chain (the one that's not referenced by any other element's nextId)
  const referencedIds = new Set([
    ...allSections.map(s => s.nextId).filter(Boolean),
    ...allResults.map(r => r.nextId).filter(Boolean)
  ]);
  
  const firstSection = allSections.find(s => !referencedIds.has(s.id));
  const firstResult = allResults.find(r => !referencedIds.has(r.id));
  
  let orderedItems: (NotebookSection | AnalysisResultType)[] = [];
  
  if (firstSection) {
    orderedItems = buildOrderedList(allSections, allResults, firstSection.id, 'notebook_section');
  } else if (firstResult) {
    orderedItems = buildOrderedList(allSections, allResults, firstResult.id, 'analysis_result');
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full p-4">
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
                    {orderedItems.length > 0 && (
                      <div className="flex-1 px-2">
                        {/* <div className="space-y-3"> */}
                          {(() => {
                            let sectionCounter = 0;
                            return orderedItems.map((item: NotebookSection | AnalysisResultType) => {
                              const isSection = 'sectionName' in item;
                              if (isSection) sectionCounter++;
                              
                              return (
                                <Fragment key={item.id}>
                                  
                                  {isSection ? (
                                    <div ref={setSectionRef(item.id)}>
                                      <SectionItem
                                        section={item}
                                        sections={allSections}
                                        projectId={projectId}
                                        analysisObjectId={analysisObjectId}
                                        depth={0}
                                        numbering={`${sectionCounter}`}
                                        onScrollToSection={handleScrollToSection}
                                        setSectionRef={setSectionRef}
                                        expandedSections={expandedSections}
                                        setExpandedSections={setExpandedSections}
                                      />
                                    </div>
                                  ) : (
                                    <div ref={setSectionRef(item.id)}>
                                      <AnalysisResult 
                                        projectId={projectId}
                                        analysisResult={item}
                                        analysisObjectId={analysisObjectId}
                                      />
                                    </div>
                                  )}
                                  
                                </Fragment>
                              );
                            });
                          })()}
                        {/* </div> */}
                      </div>
                    )}

                    {/* Empty State */}
                    {orderedItems.length === 0 && (
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