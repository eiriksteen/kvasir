'use client';

import React, { memo } from 'react';
import { Database, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '@/types/orchestrator';
import { Dataset } from '@/types/data-objects';
import { useDatasets } from '@/hooks/useDatasets';
import { UUID } from 'crypto';

interface ChatMessageBoxProps {
  message: ChatMessage;
  projectId: UUID;
}


const ChatMessageBox = memo(({ message, projectId }: ChatMessageBoxProps) => {
  const { datasets } = useDatasets(projectId);
  // const { analysisJobResults } = useAnalysis();

  const hasContext = message.context && (
    message.context.datasetIds?.length > 0 || 
    message.context.analysisIds?.length > 0 || 
    message.context.pipelineIds?.length > 0
  );

  // Different styling based on message type
  const getMessageStyles = () => {
      return {
        container: `max-w-[80%] rounded-2xl px-4 py-3 shadow-md backdrop-blur-sm ${
          message.role === 'user' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-tr-none' 
            : 'bg-gray-950/40 text-white rounded-tl-none border border-gray-800/50'
        }`,
        content: `text-xs leading-relaxed ${message.role === 'assistant' ? 'animate-fade-in' : ''}`
      };

  };

  const styles = getMessageStyles();

  return (
    <div 
      className={`mb-2 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={styles.container}>

        {hasContext && (
          <div className="mb-2 pb-2 border-b border-current/20">
            <div className="flex flex-wrap gap-1">
              {/* Datasets */}
              {message.context?.datasetIds?.map((datasetId: string) => (
                <div 
                  key={datasetId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-blue-900/50 text-blue-200"
                >
                  <Database size={10} />
                  {datasets?.find((dataset: Dataset) => dataset.id === datasetId)?.name}
                </div>
              ))}
              
              {/* Analyses */}
              {/* {message.context?.analysisIds?.map((analysisId: string) => (
                <div 
                  key={analysisId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-purple-900/50 text-purple-200"
                >
                  <BarChart size={10} />
                  {analysisJobResults?.analysesJobResults.find((analysis: AnalysisJobResultMetadata) => analysis.jobId === analysisId)?.name}
                </div>
              ))} */}
              
              {/* Automations */}
              {message.context?.pipelineIds?.map((pipelineId: string) => (
                <div 
                  key={pipelineId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-orange-900/50 text-orange-200"
                >
                  <Zap size={10} />
                  Pipeline {pipelineId.slice(0, 6)}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className={styles.content}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

// Add display name to the memo component
ChatMessageBox.displayName = 'ChatMessageBox';

export default ChatMessageBox;