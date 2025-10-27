import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, FileText, Plus, ChevronDown, ChevronUp, ExternalLink, List, Trash2, ArrowRight, Info, Calendar } from 'lucide-react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { NotebookSection, AnalysisObject, AnalysisObjectSmall } from '@/types/analysis';
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
}


const TocItem: React.FC<TocItemProps> = ({ section, level, expandedSections, onToggleExpanded, onScrollToSection, allSections }) => {
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
      <div className="flex items-center gap-2 py-2 px-2 hover:bg-gray-100 rounded transition-colors">
        <div 
          className="flex items-center gap-2 flex-1 cursor-pointer"
          onClick={() => onToggleExpanded(section.id)}
        >
          {/* <FileText size={12} className="text-gray-500 flex-shrink-0" /> */}
          <span className="text-sm text-gray-700 truncate">{section.sectionName}</span>
        </div>
        {onScrollToSection && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleScrollToSection();
            }}
            className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
            title="Scroll to section"
          >
            <ExternalLink size={12} />
          </button>
        )}
      </div>
      {isExpanded && hasChildren && (
        <div className="ml-2 border-l border-gray-300">
          <div className="">
            {orderedChildSections.map((childSection) => (
              <TocItem
                key={childSection.id}
                section={childSection as NotebookSection}
                level={level + 1}
                expandedSections={expandedSections}
                onToggleExpanded={onToggleExpanded}
                onScrollToSection={onScrollToSection}
                allSections={allSections}
              />
            ))}
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
  closeTab,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  // console.log('analysisObjectId', analysisObjectId);
  // console.log('projectId', projectId);
  const { currentAnalysisObject: analysis, deleteAnalysisObject } = useAnalysis(projectId, analysisObjectId);
  const [showCreateRootSection, setShowCreateRootSection] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showGenerateReportPopup, setShowGenerateReportPopup] = useState(false);
  const [analysisInContext, setAnalysisInContext] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const { addAnalysisToContext, removeAnalysisFromContext } = useAgentContext(projectId);

  // Function to collect all section IDs recursively
  const getAllSectionIds = (sections: NotebookSection[]): string[] => {
    const ids: string[] = [];
    sections.forEach(section => {
      ids.push(section.id);
      if (section.notebookSections) {
        ids.push(...getAllSectionIds(section.notebookSections));
      }
    });
    return ids;
  };

  // Initialize all sections as expanded when analysis data loads
  useEffect(() => {
    if (analysis?.notebook?.notebookSections && expandedSections.size === 0) {
      const allIds = getAllSectionIds(analysis.notebook.notebookSections);
      setExpandedSections(new Set(allIds));
    }
  }, [analysis]);

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

  // Function to expand all sections
  const expandAllSections = () => {
    if (!analysis?.notebook?.notebookSections) return;
    const allIds = getAllSectionIds(analysis.notebook.notebookSections);
    setExpandedSections(new Set(allIds));
  };

  // Function to collapse all sections
  const collapseAllSections = () => {
    setExpandedSections(new Set());
  };
  const expandCollapseAllSections = () => {
    if (expandedSections.size === 0) {
      expandAllSections();
    } else {
      collapseAllSections();
    }
  };

  const handleDeleteAnalysis = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirmation(true);
  };

  const handleConfirmDelete = async () => {
    await deleteAnalysisObject({analysisObjectId: analysisObjectId});
    // Close the tab for this analysis
    closeTab(analysisObjectId);
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
    return (
      <div className="w-5 bg-white border-r border-gray-300 flex grid place-items-center h-full">
        <button 
          onClick={() => setIsExpanded(true)}
          className="text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronRight size={16} />
        </button>
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
    <div className="w-64 bg-white border-r border-gray-300 flex flex-col h-full">
      {/* Header */}
      <div className="p-1 border-b border-gray-300 flex justify-center items-center flex-shrink-0 gap-1">
        {!showDetails && (
          <button
            onClick={expandCollapseAllSections}
            className="p-1 text-gray-600 hover:text-gray-900 transition-colors" 
            title="Expand all"
            >
            {(expandedSections.size === 0) ? (
              <ChevronDown size={16} />
              ) : (
              <ChevronUp size={16} />
            )}
          </button>
        )}
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
          <List size={16} />
        </button>
        <button 
          onClick={() => setIsExpanded(false)}
          className="p-1 text-gray-400 hover:text-gray-200 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft size={16} />
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
                {orderedRootSections.map((section) => (
                  <TocItem
                    key={section.id}
                    section={section as NotebookSection}
                    level={0}
                    expandedSections={expandedSections}
                    onToggleExpanded={toggleSectionExpanded}
                    onScrollToSection={onScrollToSection}
                    allSections={allSections}
                  />
                ))}
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
          analysis={analysis as AnalysisObjectSmall}
        />
      )}
    </div>
  );
};

export default TableOfContents;