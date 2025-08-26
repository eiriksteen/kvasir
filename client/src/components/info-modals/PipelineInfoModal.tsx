import { useEffect } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { X, GitMerge, Clock, ArrowDown, Database, Zap } from 'lucide-react';
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
        <p className="text-sm text-gray-400 mb-1">No functions in pipeline</p>
        <p className="text-xs text-gray-500">Add functions to see the data flow</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center space-y-1 overflow-y-auto">
      {pipeline.functions.map((functionItem, index) => {
        const isFirst = index === 0;
        const isLast = index === pipeline.functions.length - 1;
        
        return (
          <div key={functionItem.id} className="flex flex-col items-center space-y-1 w-full">
            {/* INPUT BOX */}
            {isFirst && (
              <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 border border-gray-600/30 rounded-lg p-1.5 w-fit mx-auto px-3">
                <div className="flex items-center justify-center gap-2">
                  <Database size={12} className="text-gray-400 flex-shrink-0" />
                  <span className="text-xs font-semibold text-gray-200">{functionItem.inputs[0].name}</span>
                  <span className="text-[10px] font-mono text-gray-500 bg-gray-800/50 px-1 py-0.5 rounded border border-gray-700/50">{functionItem.inputs[0].structureId}</span>
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
            <div className="bg-gradient-to-r from-orange-500/10 to-orange-600/10 border border-orange-500/30 rounded-lg p-2 w-fit mx-auto px-4 hover:border-orange-500/50 transition-all duration-200">
              <div className="flex items-center justify-center">
                <div className="flex items-center gap-2">
                  <div className="p-1 bg-orange-500/20 rounded-md">
                    <Zap size={10} className="text-orange-300" />
                  </div>
                  <h4 className="text-xs font-semibold text-gray-200">{functionItem.name}</h4>
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
            <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 border border-gray-600/30 rounded-lg p-1.5 w-fit mx-auto px-3">
              <div className="flex items-center justify-center gap-2">
                <Database size={12} className="text-gray-400 flex-shrink-0" />
                <span className="text-xs font-semibold text-gray-200">{functionItem.outputs[0].name}</span>
                <span className="text-[10px] font-mono text-gray-500 bg-gray-800/50 px-1 py-0.5 rounded border border-gray-700/50">{functionItem.outputs[0].structureId}</span>
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

  console.log(pipeline);

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
        <div className="w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden bg-black/50 rounded-lg">
          <div className="rounded-xl border-2 border-orange-500/20 shadow-xl shadow-orange-500/10 h-full flex flex-col">
            <div className="relative flex items-center p-4 border-b border-orange-500/20 flex-shrink-0">
              <div className="ml-2 flex-1">
                <h3 className="text-sm font-mono tracking-wider text-gray-200">
                  {pipeline.name}
                </h3>
                {pipeline.description && (
                  <p className="text-xs text-gray-400 mt-1">
                    {pipeline.description} • Created on {formatDate(pipeline.createdAt)}
                  </p>
                )}
              </div>
              <button
                onClick={() => onClose()}
                className="text-gray-400 hover:text-white transition-colors"
                title="Close modal"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 flex-1 overflow-hidden">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {/* Left Column - Function Chain Flow */}
                <div className="flex flex-col space-y-4 overflow-y-auto">
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-orange-500/20 rounded-xl p-4 flex flex-col flex-1 min-h-0">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-orange-500/20 rounded-lg">
                        <GitMerge className="w-4 h-4 text-orange-300" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Function Chain</h3>
                    </div>
                    <div className="flex-1 min-h-0 overflow-y-auto flex items-center justify-center">
                      <FunctionChainFlow pipeline={pipeline} />
                    </div>
                  </div>
                </div>

                {/* Right Column - Blank box */}
                <div>
                  <div className="bg-gradient-to-br from-zinc-900/80 to-zinc-800/40 border border-orange-500/20 rounded-xl p-4 h-full flex flex-col">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-orange-500/20 rounded-lg">
                        <Clock className="w-4 h-4 text-orange-300" />
                      </div>
                      <h3 className="text-sm font-semibold text-gray-200">Run Schedule</h3>
                    </div>
                    <div className="flex-1 min-h-0">
                      {/* Content for right panel can be added here */}
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