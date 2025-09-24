import { useEffect } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { X, GitMerge, Clock, ArrowDown, Database, Zap, SquarePlay, Play } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { PipelineWithFunctions } from '@/types/pipeline';

interface PipelineInfoModalProps {
  pipelineId: UUID;
  onClose: () => void;
}   

// Function Chain Flow Component
interface FunctionChainFlowProps {
  pipeline: PipelineWithFunctions;
}

function FunctionChainFlow({ pipeline }: FunctionChainFlowProps) {
  if (!pipeline.functions || pipeline.functions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <Zap size={32} className="text-orange-400/40 mb-3" />
        <p className="text-sm text-gray-600 mb-1">No functions in pipeline</p>
        <p className="text-xs text-gray-500">Add functions to see the data flow</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center space-y-1">
      {pipeline.functions.map((functionItem, index) => {
        const isFirst = index === 0;
        const isLast = index === pipeline.functions.length - 1;
        
        return (
          <div key={functionItem.id} className="flex flex-col items-center space-y-1 w-full">
            {/* INPUT BOX */}
            {isFirst && (
              <div className="bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-300 rounded-lg p-1.5 w-fit mx-auto px-3 pt-1">
                <div className="flex items-center justify-center gap-2">
                  <Database size={12} className="text-gray-600 flex-shrink-0" />
                  <span className="text-xs font-semibold text-gray-900">{functionItem.inputStructures[0].name}</span>
                  <span className="text-[10px] font-mono text-gray-600 bg-gray-200 px-1 py-0.5 rounded border border-gray-300">{functionItem.inputStructures[0].structureId}</span>
                </div>
              </div>
            )}

            {/* FLOW LINE */}
            <div className="flex flex-col items-center">
              <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/40 to-orange-500/20"></div>
              <ArrowDown size={10} className="text-orange-400/60" />
              <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/20 to-orange-500/40"></div>
            </div>

            {/* FUNCTION BOX */}
            <div className="bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-300 rounded-lg p-2 w-fit mx-auto px-4 hover:border-orange-400 transition-all duration-200">
              <div className="flex items-center justify-center">
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-orange-200 rounded-md">
                    <Zap size={10} className="text-orange-600" />
                  </div>
                  <h4 className="text-xs font-semibold text-gray-900">{functionItem.name}</h4>
                </div>
              </div>
            </div>

            {/* FLOW LINE */}
            <div className="flex flex-col items-center">
              <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/40 to-orange-500/20"></div>
              <ArrowDown size={10} className="text-orange-400/60" />
              <div className="w-0.5 h-3 bg-gradient-to-b from-orange-500/20 to-orange-500/40"></div>
            </div>

            {/* OUTPUT BOX */}
            <div className="bg-gradient-to-r from-gray-100 to-gray-50 border border-gray-300 rounded-lg p-1.5 w-fit mx-auto px-3">
              <div className="flex items-center justify-center gap-2">
                <Database size={12} className="text-gray-600 flex-shrink-0" />
                <span className="text-xs font-semibold text-gray-900">{functionItem.outputStructures[0]?.name}</span>
                <span className="text-[10px] font-mono text-gray-600 bg-gray-200 px-1 py-0.5 rounded border border-gray-300">{functionItem.outputStructures[0]?.structureId}</span>
              </div>
            </div>

            {/* SPACING BETWEEN FUNCTION CHAINS (except for last function) */}
            {!isLast && (
              <div className="h-3"></div>
            )}
          </div>
        );
      })}
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
    <>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={() => onClose()}
      />
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden bg-white rounded-lg">
          <div className="rounded-xl border-2 border-gray-300 shadow-xl h-full flex flex-col">
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
                title="Close modal"
              >
                <X size={20} />
              </button>
            </div>


            <div className="p-4 flex-1 overflow-hidden">
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-full">

                {/* Function Chain Flow */}
                <div className="lg:col-span-2 flex flex-col space-y-4 overflow-y-auto">
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <GitMerge className="w-4 h-4 text-orange-600" />
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
                        <div className="p-2 bg-orange-100 rounded-lg">
                          <SquarePlay className="w-4 h-4 text-orange-600" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-900">Runs</h3>
                      </div>

                      {/* Run Pipeline Button */}
                      <button
                        onClick={() => {
                          // TODO: Implement pipeline run functionality
                        }}
                        className="px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold text-sm rounded-lg shadow-lg hover:shadow-orange-500/25 transition-all duration-200 flex items-center gap-2 border border-orange-400/30 hover:border-orange-400/50"
                        title="Run pipeline now"
                      >
                        <Play className="w-4 h-4" />
                        Run Pipeline
                      </button>
                    </div>
                    <div className="flex-1 min-h-0">
                      {/* Content for runs can be added here */}
                    </div>
                  </div>

                  {/* Run Schedule */}
                  <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-300 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Clock className="w-4 h-4 text-orange-600" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900">Run Schedule</h3>
                    </div>
                    <div className="flex-1 min-h-0">
                      {/* Content for run schedule can be added here */}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}