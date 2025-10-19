import { useEffect, useState } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { GitMerge, Clock, ArrowDown, Database, Zap, SquarePlay, ChevronDown, ChevronRight, FileCode } from 'lucide-react';
import { Pipeline } from '@/types/pipeline';

interface PipelineInfoModalProps {
  pipelineId: UUID;
  onClose: () => void;
}   

// Function Chain Flow Component
interface FunctionChainFlowProps {
  pipeline: Pipeline;
}

function FunctionChainFlow({ pipeline }: FunctionChainFlowProps) {
  if (!pipeline.functions || pipeline.functions.length === 0) {
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
      {/* Input Object Groups */}
      {pipeline.inputObjectGroups && pipeline.inputObjectGroups.length > 0 && (
        <>
          {pipeline.inputObjectGroups.map((inputGroup) => (
            <div key={inputGroup.id} className="bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-300 rounded-lg p-1.5 w-fit mx-auto px-3 pt-1">
              <div className="flex items-center justify-center gap-2">
                <Database size={12} className="text-gray-600 flex-shrink-0" />
                <span className="text-xs font-semibold text-gray-900">{inputGroup.name}</span>
                <span className="text-[10px] font-mono text-gray-600 bg-gray-200 px-1 py-0.5 rounded border border-gray-300">{inputGroup.structureType}</span>
              </div>
            </div>
          ))}
          <div className="flex flex-col items-center">
            <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/40 to-orange-500/20"></div>
            <ArrowDown size={10} className="text-[#840B08]/70" />
            <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/20 to-orange-500/40"></div>
          </div>
        </>
      )}

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

      {/* Output Object Group Definitions */}
      {pipeline.outputObjectGroupDefinitions && pipeline.outputObjectGroupDefinitions.length > 0 && (
        <>
          <div className="flex flex-col items-center">
            <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/40 to-orange-500/20"></div>
            <ArrowDown size={10} className="text-[#840B08]/70" />
            <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/20 to-orange-500/40"></div>
          </div>
          {pipeline.outputObjectGroupDefinitions.map((outputDef) => (
            <div key={outputDef.id} className="bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-300 rounded-lg p-1.5 w-fit mx-auto px-3">
              <div className="flex items-center justify-center gap-2">
                <Database size={12} className="text-gray-600 flex-shrink-0" />
                <span className="text-xs font-semibold text-gray-900">{outputDef.name}</span>
                <span className="text-[10px] font-mono text-gray-600 bg-gray-200 px-1 py-0.5 rounded border border-gray-300">{outputDef.structureId}</span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

type SectionType = 'code' | 'runs' | 'schedule';

export default function PipelineInfoModal({ 
  pipelineId,
  onClose
}: PipelineInfoModalProps) {

  const { pipeline } = usePipeline(pipelineId);
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
                            <p className="text-sm text-gray-500">No runs yet</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Run Schedule Section */}
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleSection('schedule')}
                      className="w-full px-4 py-3 bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#840B08]/20 rounded-lg">
                          <Clock className="w-4 h-4 text-[#840B08]" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-900">Run Schedule</h3>
                      </div>
                      {openSections.has('schedule') ? (
                        <ChevronDown className="w-5 h-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-500" />
                      )}
                    </button>

                    {openSections.has('schedule') && (
                      <div className="bg-gray-50 border-t border-gray-200 p-4">
                        <div className="flex flex-col">
                          <div className="flex-1 flex flex-col items-center justify-center text-center">
                            {!pipeline.periodicSchedules || pipeline.periodicSchedules.length === 0 ? (
                              <p className="text-sm text-gray-500">No schedule set</p>
                            ) : (
                              <div className="space-y-2 w-full">
                                {pipeline.periodicSchedules.map((schedule) => (
                                  <div key={schedule.id} className="bg-white border border-gray-200 rounded-lg p-3 text-left">
                                    <p className="text-sm text-gray-700 mb-2 font-medium">{schedule.scheduleDescription}</p>
                                    <p className="text-xs text-gray-600">Cron: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{schedule.cronExpression}</span></p>
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