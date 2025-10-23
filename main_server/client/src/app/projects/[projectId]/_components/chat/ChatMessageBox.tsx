'use client';

import React, { memo } from 'react';
import { Database, Zap, Wrench } from 'lucide-react';
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
    const isToolCall = message.type === 'tool_call';
    
    return {
      container: `max-w-[95%] rounded-2xl px-2 py-1 ${
        message.role === 'user'
          ? 'px-3 py-2 rounded-tr-none'
          : isToolCall
          ? 'px-2 py-2'
          : 'px-2 py-2 border border-gray-800'
      }`,
      content: `text-xs leading-relaxed ${
        message.role === 'user' ? 'text-white' : 'text-gray-800'
      } ${message.role === 'assistant' && !isToolCall ? 'animate-fade-in' : ''}`
    };
  };

  const styles = getMessageStyles();
  const isToolCall = message.type === 'tool_call';

  return (
    <div 
      className={`mb-2 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={styles.container} style={message.role === 'user' ? { backgroundColor: '#000034' } : {}}>

        {hasContext && (
          <div className="">
            <div className="flex flex-wrap gap-1">
              {/* Datasets */}
              {message.context?.datasetIds?.map((datasetId: string) => (
                <div 
                  key={datasetId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-blue-100 text-blue-700"
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
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-orange-100 text-orange-700"
                >
                  <Zap size={10} />
                  Pipeline {pipelineId.slice(0, 6)}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {isToolCall ? (
          <div className="flex gap-2 items-start">
            <Wrench size={12} className="mt-1 flex-shrink-0 text-gray-600" />
            <div className={styles.content}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className={styles.content}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
});

// Add display name to the memo component
ChatMessageBox.displayName = 'ChatMessageBox';

export default ChatMessageBox;