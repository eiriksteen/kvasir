import { useEffect, useState } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { GitMerge, Zap, SquarePlay, ChevronDown, ChevronRight, FileCode } from 'lucide-react';
import { Pipeline } from '@/types/pipeline';

interface PipelineInfoTabProps {
  pipelineId: UUID;
  projectId: UUID;
  onClose: () => void;
}   

// Function Chain Flow Component
interface FunctionChainFlowProps {
  pipeline: Pipeline;
}

function FunctionChainFlow({ pipeline }: FunctionChainFlowProps) {
  if (!pipeline.implementation) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <Zap size={32} className="text-[#840B08]/60 mb-3" />
        <p className="text-sm text-gray-600 mb-1">Implementation In Progress</p>
        <p className="text-xs text-gray-500">The pipeline is being generated</p>
      </div>
    );
  }

  if (!pipeline.implementation.functions || pipeline.implementation.functions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <Zap size={32} className="text-[#840B08]/60 mb-3" />
        <p className="text-sm text-gray-600 mb-1">No functions in pipeline</p>
        <p className="text-xs text-gray-500">Add functions to see the data flow</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center space-y-1">
      {/* Pipeline Function */}
      <div className="bg-gradient-to-r from-[#840B08]/10 to-[#840B08]/20 border border-[#840B08]/30 rounded-lg p-2 w-fit mx-auto px-4 hover:border-[#840B08]/50 transition-all duration-200">
        <div className="flex items-center justify-center">
          <div className="flex items-center gap-2">
            <div className="p-1 bg-[#840B08]/30 rounded-md">
              <Zap size={10} className="text-[#840B08]" />
            </div>
            <h4 className="text-xs font-semibold text-gray-900">{pipeline.name}</h4>
          </div>
        </div>
      </div>
    </div>
  );
}

type SectionType = 'code' | 'runs';

export default function PipelineInfoTab({ 
  pipelineId,
  projectId,
  onClose
}: PipelineInfoTabProps) {

  const { pipeline } = usePipeline(pipelineId, projectId);
  const [openSections, setOpenSections] = useState<Set<SectionType>>(new Set());

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [onClose]);

  const toggleSection = (section: SectionType) => {
    setOpenSections(prev => {
      const newSections = new Set(prev);
      if (newSections.has(section)) {
        newSections.delete(section);
      } else {
        newSections.add(section);
      }
      return newSections;
    });
  };

  if (!pipeline) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Content Section */}
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Full Width Description */}
              <div className="p-4 w-full">
                {pipeline.description ? (
                  <p className="text-sm text-gray-700">
                    {pipeline.description}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">No description provided</p>
                )}
              </div>

              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start h-[70vh]">
                {/* Left Column: Function Chain (Always Visible) */}
                <div className="bg-gray-50 rounded-xl p-4 flex flex-col h-full">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-[#840B08]/20 rounded-lg">
                      <GitMerge className="w-4 h-4 text-[#840B08]" />
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900">Function Chain</h3>
                  </div>
                  <div className="flex-1 overflow-y-auto grid place-items-center">
                    <FunctionChainFlow pipeline={pipeline} />
                  </div>
                </div>

                {/* Right Column: Collapsible Sections */}
                <div className="space-y-2 h-full overflow-y-auto">
                  {/* Code Section */}
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleSection('code')}
                      className="w-full px-4 py-3 bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#840B08]/20 rounded-lg">
                          <FileCode className="w-4 h-4 text-[#840B08]" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-900">Code</h3>
                      </div>
                      {openSections.has('code') ? (
                        <ChevronDown className="w-5 h-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-500" />
                      )}
                    </button>
                    
                    {openSections.has('code') && (
                      <div className="bg-gray-50 border-t border-gray-200 p-4">
                        <div className="flex flex-col">
                          <div className="flex-1 flex flex-col items-center justify-center text-center">
                            <p className="text-sm text-gray-500">Code view coming soon</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Runs Section */}
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleSection('runs')}
                      className="w-full px-4 py-3 bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#840B08]/20 rounded-lg">
                          <SquarePlay className="w-4 h-4 text-[#840B08]" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-900">Runs</h3>
                      </div>
                      {openSections.has('runs') ? (
                        <ChevronDown className="w-5 h-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-500" />
                      )}
                    </button>

                    {openSections.has('runs') && (
                      <div className="bg-gray-50 border-t border-gray-200 p-4">
                        <div className="flex flex-col">
                          <div className="flex-1 flex flex-col items-center justify-center text-center">
                            {!pipeline.implementation || !pipeline.implementation.runs || pipeline.implementation.runs.length === 0 ? (
                              <p className="text-sm text-gray-500">No runs yet</p>
                            ) : (
                              <div className="space-y-2 w-full">
                                {pipeline.implementation.runs.map((run) => (
                                  <div key={run.id} className="bg-white border border-gray-200 rounded-lg p-3 text-left">
                                    <p className="text-sm text-gray-700 mb-2 font-medium">Run {run.id.slice(0, 8)}</p>
                                    <p className="text-xs text-gray-600">Status: <span className={`font-mono px-2 py-1 rounded ${run.status === 'completed' ? 'bg-green-100 text-green-800' : run.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>{run.status}</span></p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}