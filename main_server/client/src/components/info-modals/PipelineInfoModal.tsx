import { useEffect } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { X, GitMerge, Clock, ArrowDown, Database, Zap, SquarePlay, Play } from 'lucide-react';
import { formatDate } from '@/lib/utils';
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

export default function PipelineInfoModal({ 
  pipelineId,
  onClose
}: PipelineInfoModalProps) {

  const { pipeline } = usePipeline(pipelineId);

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

  if (!pipeline) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          {/* Header Section */}
          <div className="relative flex items-center p-6 border-b border-gray-300 flex-shrink-0">
            <div className="flex-1">
              <h3 className="text-sm font-mono tracking-wider text-gray-900">
                {pipeline.name}
              </h3>
              {pipeline.description && (
                <p className="text-xs text-gray-600 mt-1">
                  {pipeline.description} • Created on {formatDate(pipeline.createdAt)}
                </p>
              )}
            </div>

            <button
              onClick={() => onClose()}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              title="Close tab"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content Section */}
          <div className="flex-1 min-h-0">
            <div className="h-full p-4">
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-full">
                {/* Function Chain Flow */}
                <div className="lg:col-span-2 flex flex-col space-y-4 overflow-y-auto">
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-[#840B08]/20 rounded-lg">
                        <GitMerge className="w-4 h-4 text-[#840B08]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Function Chain</h3>
                    </div>
                    <div className="flex-1 min-h-0 overflow-y-auto grid place-items-center">
                      <FunctionChainFlow pipeline={pipeline} />
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-2 flex flex-col space-y-4">
                  {/* Runs */}
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#840B08]/20 rounded-lg">
                          <SquarePlay className="w-4 h-4 text-[#840B08]" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-900">Runs</h3>
                      </div>

                      {/* Run Pipeline Button */}
                      <button
                        onClick={() => {
                          // TODO: Implement pipeline run functionality
                        }}
                        className="px-4 py-2 bg-gradient-to-r from-[#840B08] to-[#840B08]/80 hover:from-[#840B08]/80 hover:to-[#840B08] text-white font-semibold text-sm rounded-lg shadow-lg hover:shadow-[#840B08]/25 transition-all duration-200 flex items-center gap-2"
                        title="Run pipeline now"
                      >
                        <Play className="w-4 h-4" />
                        Run Pipeline
                      </button>
                    </div>
                    <div className="flex-1 min-h-0 flex flex-col items-center justify-center text-center">
                      <p className="text-sm text-gray-500">No runs yet</p>
                    </div>
                  </div>

                  {/* Run Schedule */}
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-[#840B08]/20 rounded-lg">
                        <Clock className="w-4 h-4 text-[#840B08]" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Run Schedule</h3>
                    </div>
                    <div className="flex-1 min-h-0 flex flex-col items-center justify-center text-center">
                      {!pipeline.periodicSchedules || pipeline.periodicSchedules.length === 0 ? (
                        <p className="text-sm text-gray-500">No schedule set</p>
                      ) : (
                        <div className="space-y-2 w-full">
                          {pipeline.periodicSchedules.map((schedule) => (
                            <div key={schedule.id} className="bg-gray-50 border border-gray-200 rounded-lg p-2">
                              <p className="text-xs text-gray-600 mb-1">{schedule.scheduleDescription}</p>
                              <p className="text-xs text-gray-600">Cron: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{schedule.cronExpression}</span></p>
                            </div>
                          ))}
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
    </div>
  );
}