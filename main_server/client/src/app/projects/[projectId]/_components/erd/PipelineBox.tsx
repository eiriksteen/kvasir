import React, { useState } from 'react';
import { Zap, Play } from 'lucide-react';
import { useMountedPipeline } from '@/hooks/useOntology';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';
import RunPipelineModal from '@/components/RunPipelineModal';

interface PipelineBoxProps {
  pipelineId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function PipelineBox({ pipelineId, projectId, openTab }: PipelineBoxProps) {
  const pipeline = useMountedPipeline(pipelineId, projectId);

  const { 
    pipelinesInContext, 
    addPipelineToContext, 
    removePipelineFromContext 
  } = useAgentContext(projectId);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const isInContext = pipelinesInContext.includes(pipelineId);

  const handleRunPipeline = (config: {
    args: Record<string, unknown>;
    inputs: {
      dataSourceIds: UUID[];
      datasetIds: UUID[];
      modelInstantiatedIds: UUID[];
    };
    name?: string;
    description?: string;
  }) => {
    console.log(config);
  };

  const handleMainBoxClick = (event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Cmd+click or Ctrl+click - add to context
      if (isInContext) {
        removePipelineFromContext(pipelineId);
      } else {
        addPipelineToContext(pipelineId);
      }
    } else {
      // Regular click - open tab to overview
      openTab(pipelineId, true, 'overview');
    }
  };

  if (!pipeline) {
    return null;
  }

  const hasRuns = pipeline.runs && pipeline.runs.length > 0;
  const runsCount = pipeline.runs?.length || 0;

  const handleRunsBoxClick = (event: React.MouseEvent) => {
    event.stopPropagation();
    openTab(pipelineId, true, 'runs');
  };
  
  return (
    <>
      <div className={`flex shadow-md rounded-md min-w-[100px] max-w-[240px] overflow-hidden ${
        isInContext 
          ? 'ring-2 ring-[#840B08]/30' 
          : ''
      }`}>
        <div
          className={`px-3 py-3 flex-1 min-w-0 cursor-pointer border-2 border-r-0 rounded-l-md ${
            isInContext
              ? 'border-[#840B08] bg-[#840B08]/10 hover:bg-[#840B08]/15'
              : 'border-[#840B08] hover:bg-[#840B08]/10'
          }`}
          onClick={handleMainBoxClick}
        >
          <div className="flex flex-col">
            <div className="flex items-center mb-2">
              <div className="rounded-full w-6 h-6 flex items-center justify-center bg-[#840B08]/10 border border-[#840B08]/30 mr-2">
                <Zap className="w-3 h-3 text-[#840B08]" />
              </div>
              <div className="text-[#840B08] font-mono text-xs">Pipeline</div>
            </div>
            <div>
              <div className="text-xs font-mono text-gray-800 break-words">{pipeline.name}</div>
            </div>
          </div>
        </div>
        
        {/* Runs info box - glued to the right of pipeline box */}
        <div 
          onClick={handleRunsBoxClick}
          className={`flex flex-col items-center justify-center px-2 py-2 border-l-2 border-t-2 border-r-2 border-b-2 rounded-r-md cursor-pointer transition-colors ${
            hasRuns 
              ? 'border-l-[#840B08] border-t-[#840B08] border-r-[#840B08] border-b-[#840B08] border-t-dashed border-r-dashed border-b-dashed bg-[#840B08]/5 hover:bg-[#840B08]/15' 
              : 'border-l-[#840B08]/30 border-t-[#840B08]/30 border-r-[#840B08]/30 border-b-[#840B08]/30 border-t-dashed border-r-dashed border-b-dashed bg-gray-50 hover:bg-gray-100'
          }`}
        >
          <div className="flex items-center justify-center mb-1">
            <Play className={`w-4 h-4 ${hasRuns ? 'text-[#840B08] fill-[#840B08]' : 'text-gray-400 fill-gray-400'}`} />
          </div>
          <div className={`text-[10px] font-mono whitespace-nowrap ${hasRuns ? 'text-[#840B08]' : 'text-gray-400'}`}>
            runs ({runsCount})
          </div>
        </div>
      </div>
      
      {pipeline && (
        <RunPipelineModal
          pipeline={pipeline}
          projectId={projectId}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onRunPipeline={handleRunPipeline}
        />
      )}
    </>
  );
}
