import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, FileText, Plus, Trash2, ArrowRight, Info, Calendar } from 'lucide-react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { Section } from '@/types/ontology/analysis';
import SectionItemCreate from '@/components/info-tabs/analysis/SectionItemCreate';
import { UUID } from 'crypto';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import GenerateReportPopup from '@/components/info-tabs/analysis/GenerateReportPopup';
import { useAgentContext } from '@/hooks/useAgentContext';

interface TableOfContentsProps {
  analysisObjectId: UUID;
  projectId: UUID;
  onScrollToSection?: (sectionId: string) => void;
}

interface TocItemProps {
  section: Section;
  level: number;
  expandedSections: Set<string>;
  onToggleExpanded: (sectionId: string) => void;
  onScrollToSection?: (sectionId: string) => void;
  allSections: Section[];
  numbering: string;
}


const TocItem: React.FC<TocItemProps> = ({ section, level, onScrollToSection, numbering }) => {
  // Handle scroll to section
  const handleScrollToSection = () => {
    if (!onScrollToSection) return;
    onScrollToSection(section.id);
  };

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
          <span className={`${level === 0 ? 'text-sm' : 'text-xs'} text-gray-700 truncate text-left`}>{section.name}</span>
          </div>
        </div>
      </div>
      {/* Note: New structure doesn't support nested sections, so no children to render */}
    </div>
  );
};

const TableOfContents: React.FC<TableOfContentsProps> = ({
  analysisObjectId,
  projectId,
  onScrollToSection,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { analysis } = useAnalysis(projectId, analysisObjectId);
  const [showCreateRootSection, setShowCreateRootSection] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showGenerateReportPopup, setShowGenerateReportPopup] = useState(false);
  const [analysisInContext, setAnalysisInContext] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const { addAnalysisToContext, removeAnalysisFromContext } = useAgentContext(projectId);

  // Initialize all sections as expanded when analysis data loads
  useEffect(() => {
    if (analysis?.sections && expandedSections.size === 0) {
      const allIds = analysis.sections.map(s => s.id);
      setExpandedSections(new Set(allIds));
    }
  }, [analysis, expandedSections.size]);

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
    // TODO: Implement delete analysis API call
    console.log('Delete analysis:', analysisObjectId);
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

  // Get sections ordered by creation date
  const orderedSections = analysis?.sections 
    ? [...analysis.sections].sort((a, b) => (a.createdAt < b.createdAt ? -1 : 1))
    : [];

  // Early return for collapsed state
  if (!isExpanded) {
    return (
      <div className="bg-white border-r border-gray-300 flex flex-col h-full">
        <div className="font-mono text-xs flex flex-col items-center px-3 py-3 h-full">
          <div className="flex-1 flex flex-col justify-center">
            {showDetails ? (
              <div className="w-full">
                <DetailsView />
              </div>
            ) : (
              orderedSections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => onScrollToSection?.(section.id)}
                  className="text-xs font-mono text-gray-400 hover:text-gray-900 transition-colors mb-3 cursor-pointer"
                >
                  {index + 1}
                </button>
              ))
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
            {orderedSections.length > 0 ? (
              <div className="">
                {orderedSections.map((section, index) => (
                  <TocItem
                    key={section.id}
                    section={section}
                    level={0}
                    expandedSections={expandedSections}
                    onToggleExpanded={toggleSectionExpanded}
                    onScrollToSection={onScrollToSection}
                    allSections={orderedSections}
                    numbering={`${index + 1}`}
                  />
                ))}
                {showCreateRootSection && (
                  <div className="mb-4">
                    <SectionItemCreate
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
          analysis={analysis}
          projectId={projectId}
        />
      )}
    </div>
  );
};

export default TableOfContents;