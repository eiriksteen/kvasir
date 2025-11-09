import React, { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, FileText, Plus, Trash2, ArrowRight, Info, Calendar } from 'lucide-react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { NotebookSection, AnalysisSmall } from '@/types/analysis';
import SectionItemCreate from '@/components/info-tabs/analysis/SectionItemCreate';
import { buildOrderedSectionsList, findParentSections } from '@/lib/utils';
import { UUID } from 'crypto';
import { AnalysisResult as AnalysisResultType } from '@/types/analysis';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import GenerateReportPopup from '@/components/info-tabs/analysis/GenerateReportPopup';
import { useAgentContext } from '@/hooks/useAgentContext';

interface TableOfContentsProps {
  analysisObjectId: UUID;
  projectId: UUID;
  onScrollToSection?: (sectionId: string) => void;
  closeTab: (id: UUID | null) => void;
}

interface TocItemProps {
  section: NotebookSection;
  level: number;
  expandedSections: Set<string>;
  onToggleExpanded: (sectionId: string) => void;
  onScrollToSection?: (sectionId: string) => void;
  allSections: NotebookSection[];
  numbering: string;
}


const TocItem: React.FC<TocItemProps> = ({ section, level, expandedSections, onToggleExpanded, onScrollToSection, allSections, numbering }) => {
  const isExpanded = expandedSections.has(section.id);
  
  
  // Handle scroll to section with parent expansion
  const handleScrollToSection = () => {
    if (!onScrollToSection) return;
    
    // Find all parent sections that need to be expanded
    const parentIds = findParentSections(section.id, allSections);
    
    // Expand all parent sections
    parentIds.forEach(parentId => {
      if (!expandedSections.has(parentId)) {
        onToggleExpanded(parentId);
      }
    });
    
    // Scroll to the section (this will also trigger expansion in main content)
    onScrollToSection(section.id);
  };
  

  
  // Build ordered list using the new nextType/nextId system
  const childSections = section.notebookSections || [];
  const allResults = allSections.flatMap(section => section.analysisResults || []);
  
  // Find the first element in the chain (the one that's not referenced by any other element's nextId)
  const referencedIds = new Set([
    ...childSections.map(s => s.nextId).filter(Boolean),
    ...allResults.map(r => r.nextId).filter(Boolean)
  ]);
  
  const firstSection = childSections.find(s => !referencedIds.has(s.id));
  const firstResult = allResults.find(r => !referencedIds.has(r.id));
  
  let orderedChildSections: (NotebookSection | AnalysisResultType)[] = [];
  
  if (firstSection) {
    orderedChildSections = buildOrderedSectionsList(childSections, allResults, firstSection.id, 'notebook_section');
  } else if (firstResult) {
    orderedChildSections = buildOrderedSectionsList(childSections, allResults, firstResult.id, 'analysis_result');
  }
  
  const hasChildren = orderedChildSections.length > 0;

  return (
    <div className="w-full">
      <div className="group">
        <div 
          className="flex items-center gap-2 py-2 px-2 hover:bg-gray-100 rounded transition-colors cursor-pointer"
          onClick={handleScrollToSection}
        >
        <div className="flex items-center flex-1 text-left">
          <span className={`${level === 0 ? 'text-xs' : 'text-xs'} font-mono text-gray-500 flex-shrink-0 ${level === 0 ? 'min-w-[1.5rem]' : 'min-w-[2rem]'}`}>
            {numbering}
          </span>
          <span className={`${level === 0 ? 'text-sm' : 'text-xs'} text-gray-700 truncate text-left`}>{section.sectionName}</span>
          </div>
        </div>
      </div>
      {isExpanded && hasChildren && (
        <div className="ml-2 border-l border-gray-300">
          <div className="">
            {(() => {
              let childCounter = 0;
              return orderedChildSections.map((childSection) => {
                const isSection = 'sectionName' in childSection;
                if (isSection) childCounter++;
                return (
                  <TocItem
                    key={childSection.id}
                    section={childSection as NotebookSection}
                    level={level + 1}
                    expandedSections={expandedSections}
                    onToggleExpanded={onToggleExpanded}
                    onScrollToSection={onScrollToSection}
                    allSections={allSections}
                    numbering={`${numbering}.${childCounter}`}
                  />
                );
              });
            })()}
          </div>
        </div>
      )}
    </div>
  );
};

const TableOfContents: React.FC<TableOfContentsProps> = ({
  analysisObjectId,
  projectId,
  onScrollToSection,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { currentAnalysisObject: analysis, deleteAnalysisObject } = useAnalysis(projectId, analysisObjectId);
  const [showCreateRootSection, setShowCreateRootSection] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showGenerateReportPopup, setShowGenerateReportPopup] = useState(false);
  const [analysisInContext, setAnalysisInContext] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const { addAnalysisToContext, removeAnalysisFromContext } = useAgentContext(projectId);

  // Function to collect all section IDs recursively
  const getAllSectionIds = useCallback((sections: NotebookSection[]): string[] => {
    const ids: string[] = [];
    sections.forEach(section => {
      ids.push(section.id);
      if (section.notebookSections) {
        ids.push(...getAllSectionIds(section.notebookSections));
      }
    });
    return ids;
  }, []);

  // Initialize all sections as expanded when analysis data loads
  useEffect(() => {
    if (analysis?.notebook?.notebookSections && expandedSections.size === 0) {
      const allIds = getAllSectionIds(analysis.notebook.notebookSections);
      setExpandedSections(new Set(allIds));
    }
  }, [analysis, expandedSections.size, getAllSectionIds]);

  // Function to toggle a single section's expanded state
  const toggleSectionExpanded = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };


  const handleDeleteAnalysis = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirmation(true);
  };

  const handleConfirmDelete = async () => {
    await deleteAnalysisObject({analysisObjectId: analysisObjectId});
    setShowDeleteConfirmation(false);
  };

  const handleAddAnalysisToContext = async () => {
    if (!analysis) return;
    
    if (analysisInContext) {
      await removeAnalysisFromContext(analysis.id);
      setAnalysisInContext(false);
    }
    else {
      await addAnalysisToContext(analysis.id);
      setAnalysisInContext(true);
    }
  };

  const toggleDetailsView = () => {
    setShowDetails(!showDetails);
  };

  // Details view component
  const DetailsView = () => (
    <div className="space-y-2">
      
      <div className="space-y-1">
        <div className="p-2 hover:bg-gray-100 rounded transition-colors">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <FileText size={14} />
            <span className="truncate">{analysis?.name || 'Untitled Analysis'}</span>
          </div>
        </div>
        
        <div className="p-2 hover:bg-gray-100 rounded transition-colors">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Calendar size={14} />
            <span>Created: {analysis?.createdAt ? new Date(analysis.createdAt).toLocaleDateString() : 'Unknown'}</span>
          </div>
        </div>
        
        {analysis?.description && (
          <div className="p-2 hover:bg-gray-100 rounded transition-colors">
            <div className="flex items-start gap-2 text-sm text-gray-700">
              <Info size={14} className="mt-0.5 flex-shrink-0" />
              <span className="text-xs">{analysis.description}</span>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-2 border-t border-gray-300 mt-4">
        <h4 className="text-xs font-medium text-gray-600 mb-2">Actions</h4>
        <div className="space-y-1">
          <button
            onClick={handleAddAnalysisToContext}
            className="w-full p-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-2"
          >
            <ArrowRight size={14} className={`${analysisInContext ? 'rotate-180' : ''}`} />
            {analysisInContext ? 'Remove from context' : 'Add to context'}
          </button>
          
          <button
            onClick={() => setShowGenerateReportPopup(true)}
            className="w-full p-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-2"
          >
            <FileText size={14} />
            Generate PDF report
          </button>
          
          <button
            onClick={handleDeleteAnalysis}
            className="w-full p-2 text-left text-sm text-red-600 hover:bg-gray-100 rounded flex items-center gap-2"
          >
            <Trash2 size={14} />
            Delete analysis
          </button>
        </div>
      </div>
    </div>
  );

  if (!analysis) {
    return (
      <div className="w-64 bg-white border-r border-gray-300 p-4 h-full flex items-center justify-center">
        <div className="text-center">
          <FileText size={32} className="mx-auto text-gray-600 mb-2" />
          <p className="text-gray-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // Early return for collapsed state
  if (!isExpanded) {
    // Get ordered root sections for display
    const allSections = analysis?.notebook?.notebookSections || [];
    const allResults = allSections.flatMap(section => section.analysisResults || []);
    
    // Find the first element in the chain
    const referencedIds = new Set([
      ...allSections.map(s => s.nextId).filter(Boolean),
      ...allResults.map(r => r.nextId).filter(Boolean)
    ]);
    
    const firstSection = allSections.find(s => !referencedIds.has(s.id));
    const firstResult = allResults.find(r => !referencedIds.has(r.id));
    
    let orderedRootSections: (NotebookSection | AnalysisResultType)[] = [];
    
    if (firstSection) {
      orderedRootSections = buildOrderedSectionsList(allSections, allResults, firstSection.id, 'notebook_section');
    } else if (firstResult) {
      orderedRootSections = buildOrderedSectionsList(allSections, allResults, firstResult.id, 'analysis_result');
    }
    
    return (
      <div className="bg-white border-r border-gray-300 flex flex-col h-full">
        <div className="font-mono text-xs flex flex-col items-center px-3 py-3 h-full">
          <div className="flex-1 flex flex-col justify-center">
            {showDetails ? (
              <div className="w-full">
                <DetailsView />
              </div>
            ) : (
              (() => {
                let sectionCounter = 0;
                return orderedRootSections.map((item) => {
                  const isSection = 'sectionName' in item;
                  if (isSection) sectionCounter++;
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => onScrollToSection?.(item.id)}
                      className="text-xs font-mono text-gray-400 hover:text-gray-900 transition-colors mb-3 cursor-pointer"
                    >
                      {sectionCounter}
                    </button>
                  );
                });
              })()
            )}
          </div>
          <button 
            onClick={() => setIsExpanded(true)}
            className="text-gray-600 hover:text-gray-900 transition-colors mt-2"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    );
  }

  // Build ordered list for root sections using the nextType/nextId system
  const allSections = analysis.notebook?.notebookSections || [];
  
  // Find the first root section in the chain (the one that's not referenced by any other section's nextId)
  const allResults = allSections.flatMap(section => section.analysisResults || []);
  
  // Find the first element in the chain (the one that's not referenced by any other element's nextId)
  const referencedIds = new Set([
    ...allSections.map(s => s.nextId).filter(Boolean),
    ...allResults.map(r => r.nextId).filter(Boolean)
  ]);
  
  const firstSection = allSections.find(s => !referencedIds.has(s.id));
  const firstResult = allResults.find(r => !referencedIds.has(r.id));
  
  let orderedRootSections: (NotebookSection | AnalysisResultType)[] = [];
  
  if (firstSection) {
    orderedRootSections = buildOrderedSectionsList(allSections, allResults, firstSection.id, 'notebook_section');
  } else if (firstResult) {
    orderedRootSections = buildOrderedSectionsList(allSections, allResults, firstResult.id, 'analysis_result');
  }

  return (
    <div className="w-56 bg-white border-r border-gray-300 flex flex-col h-full">
      {/* Header */}
      <div className="p-1 border-b border-gray-300 flex justify-center items-center flex-shrink-0 gap-1">
        {!showDetails && (
          <button
            onClick={() => setShowCreateRootSection(!showCreateRootSection)}
            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
            title="Add section"
          >
            <Plus size={16} />
          </button>
        )}
         {/* Toggle details view */}
         <button
          onClick={toggleDetailsView}
          className="p-1 text-gray-400 hover:text-gray-200 transition-colors"
          title={showDetails ? "Show table of contents" : "Show details"}
        >
          <Info size={16} />
        </button>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2 min-h-0">
        {showDetails ? (
          <DetailsView />
        ) : (
          <>
            {orderedRootSections.length > 0 ? (
              <div className="">
                {(() => {
                  let rootCounter = 0;
                  return orderedRootSections.map((section) => {
                    const isSection = 'sectionName' in section;
                    if (isSection) rootCounter++;
                    return (
                      <TocItem
                        key={section.id}
                        section={section as NotebookSection}
                        level={0}
                        expandedSections={expandedSections}
                        onToggleExpanded={toggleSectionExpanded}
                        onScrollToSection={onScrollToSection}
                        allSections={allSections}
                        numbering={`${rootCounter}`}
                      />
                    );
                  });
                })()}
                {showCreateRootSection && (
                  <div className="mb-4">
                    <SectionItemCreate
                      parentId={null}
                      projectId={projectId}
                      analysisObjectId={analysisObjectId}
                      onCancel={() => setShowCreateRootSection(false)}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div>
                {showCreateRootSection && (
                  <div className="mb-4">
                    <SectionItemCreate
                      parentId={null}
                      projectId={projectId}
                      analysisObjectId={analysisObjectId}
                      onCancel={() => setShowCreateRootSection(false)}
                    />
                  </div>
                )}
                <div className="text-center py-8">
                  <FileText size={24} className="mx-auto text-gray-600 mb-2" />
                  <p className="text-gray-500 text-xs">No sections yet</p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
      
      {/* Footer with collapse button */}
      <div className="p-1 border-t border-gray-300 flex justify-end items-center flex-shrink-0">
        <button 
          onClick={() => setIsExpanded(false)}
          className="p-1 text-gray-400 hover:text-gray-200 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft size={16} />
        </button>
      </div>
      
      {/* Popups */}
      <ConfirmationPopup
        isOpen={showDeleteConfirmation}
        message="Are you sure you want to delete this analysis? This action cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirmation(false)}
      />
      {analysis && (
        <GenerateReportPopup
          isOpen={showGenerateReportPopup}
          onClose={() => setShowGenerateReportPopup(false)}
          analysis={analysis as AnalysisSmall}
          projectId={projectId}
        />
      )}
    </div>
  );
};

export default TableOfContents;