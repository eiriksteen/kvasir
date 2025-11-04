import React, { useState } from 'react';
import { Zap } from 'lucide-react';
import { usePipeline } from '@/hooks/usePipelines';
import { useAgentContext } from '@/hooks/useAgentContext';
import { UUID } from 'crypto';
import RunPipelineModal from '@/components/RunPipelineModal';

interface PipelineBoxProps {
  pipelineId: UUID;
  projectId: UUID;
  openTab: (id: UUID | null, closable?: boolean, initialView?: 'overview' | 'code' | 'runs') => void;
}

export default function PipelineBox({ pipelineId, projectId, openTab }: PipelineBoxProps) {
  const { pipeline, triggerRunPipeline } = usePipeline(pipelineId, projectId);

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
      modelEntityIds: UUID[];
    };
    name?: string;
    description?: string;
  }) => {
    triggerRunPipeline(config);
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
  
  return (
    <>
      <div className={`flex shadow-md border-2 rounded-md min-w-[100px] max-w-[300px] overflow-hidden ${
        isInContext 
          ? 'border-[#840B08] bg-[#840B08]/10 ring-2 ring-[#840B08]/30' 
          : 'border-[#840B08]'
      }`}>
        <div
          className="px-3 py-3 flex-1 min-w-0 cursor-pointer hover:bg-[#840B08]/10"
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
              <div className="text-xs font-mono text-gray-800 truncate">{pipeline.name}</div>
            </div>
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
