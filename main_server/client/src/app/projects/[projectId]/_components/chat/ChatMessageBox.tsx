'use client';

import React, { memo, ReactNode } from 'react';
import { Wrench } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '@/types/orchestrator';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { Pipeline } from '@/types/pipeline';
import { ModelEntity } from '@/types/model';
import { AnalysisSmall } from '@/types/analysis';
import { useDatasets, useDataSources, usePipelines, useModelEntities, useAnalyses } from '@/hooks';
import { DataSourceMini, DatasetMini, AnalysisMini, PipelineMini, ModelEntityMini } from '@/components/entity-mini';
import { MarkdownComponents } from '@/components/MarkdownComponents';
import { UUID } from 'crypto';

interface ChatMessageBoxProps {
  message: ChatMessage;
  projectId: UUID;
}

interface BaseComponentProps {
  children?: ReactNode;
  className?: string;
  [key: string]: unknown;
}

// Chat-specific markdown components - override only what's different (smaller fonts, list-outside)
const ChatMarkdownComponents = {
  ...MarkdownComponents,
  p: ({ children, ...props }: BaseComponentProps) => (
    <p className="text-xs leading-relaxed" {...props}>{children}</p>
  ),
  ul: ({ children, ...props }: BaseComponentProps) => (
    <ul className="text-xs list-disc list-outside space-y-0.5 my-0.5 ml-4 pl-2" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }: BaseComponentProps) => (
    <ol className="text-xs list-decimal list-outside space-y-0.5 my-0.5 ml-4 pl-2" {...props}>{children}</ol>
  ),
  li: ({ children, ...props }: BaseComponentProps) => (
    <li className="text-xs leading-relaxed" {...props}>{children}</li>
  ),
  h1: ({ children, ...props }: BaseComponentProps) => (
    <h1 className="text-sm font-bold my-1 text-gray-900" {...props}>{children}</h1>
  ),
  h2: ({ children, ...props }: BaseComponentProps) => (
    <h2 className="text-xs font-semibold my-1 text-gray-900" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }: BaseComponentProps) => (
    <h3 className="text-xs font-semibold my-0.5 text-gray-900" {...props}>{children}</h3>
  ),
  h4: ({ children, ...props }: BaseComponentProps) => (
    <h4 className="text-xs font-medium my-0.5 text-gray-900" {...props}>{children}</h4>
  ),
  h5: ({ children, ...props }: BaseComponentProps) => (
    <h5 className="text-xs font-medium my-0.5 text-gray-900" {...props}>{children}</h5>
  ),
  h6: ({ children, ...props }: BaseComponentProps) => (
    <h6 className="text-xs font-medium my-0.5 text-gray-900" {...props}>{children}</h6>
  ),
};


const ChatMessageBox = memo(({ message, projectId }: ChatMessageBoxProps) => {
  const { dataSources } = useDataSources(projectId);
  const { datasets } = useDatasets(projectId);
  const { pipelines } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalyses(projectId);

  const hasContext = message.role !== 'user' && message.context && (
    message.context.dataSourceIds?.length > 0 ||
    message.context.datasetIds?.length > 0 || 
    message.context.analysisIds?.length > 0 || 
    message.context.pipelineIds?.length > 0 ||
    message.context.modelEntityIds?.length > 0
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
          : 'px-2 py-2 bg-white'
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
          <div className="mb-2">
            <div className="flex flex-wrap gap-1">
              {/* Data Sources */}
              {message.context?.dataSourceIds?.map((dataSourceId: string) => {
                const dataSource = dataSources?.find((ds: DataSource) => ds.id === dataSourceId);
                return dataSource ? (
                  <DataSourceMini key={dataSourceId} name={dataSource.name} size="sm" />
                ) : null;
              })}
              
              {/* Datasets */}
              {message.context?.datasetIds?.map((datasetId: string) => {
                const dataset = datasets?.find((ds: Dataset) => ds.id === datasetId);
                return dataset ? (
                  <DatasetMini key={datasetId} name={dataset.name} size="sm" />
                ) : null;
              })}
              
              {/* Analyses */}
              {message.context?.analysisIds?.map((analysisId: string) => {
                const analysis = analysisObjects?.find((a: AnalysisSmall) => a.id === analysisId);
                return analysis ? (
                  <AnalysisMini key={analysisId} name={analysis.name} size="sm" />
                ) : null;
              })}
              
              {/* Pipelines */}
              {message.context?.pipelineIds?.map((pipelineId: string) => {
                const pipeline = pipelines?.find((p: Pipeline) => p.id === pipelineId);
                return pipeline ? (
                  <PipelineMini key={pipelineId} name={pipeline.name} size="sm" />
                ) : null;
              })}
              
              {/* Model Entities */}
              {message.context?.modelEntityIds?.map((modelEntityId: string) => {
                const modelEntity = modelEntities?.find((m: ModelEntity) => m.id === modelEntityId);
                return modelEntity ? (
                  <ModelEntityMini key={modelEntityId} name={modelEntity.name} size="sm" />
                ) : null;
              })}
            </div>
          </div>
        )}
        
        {isToolCall ? (
          <div className="flex gap-2 items-start">
            <Wrench size={12} className="mt-1 flex-shrink-0 text-gray-600" />
            <div className={styles.content}>
              {/* @ts-expect-error - MarkdownComponents type mismatch with react-markdown */}
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={ChatMarkdownComponents}>
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className={styles.content}>
            {/* @ts-expect-error - MarkdownComponents type mismatch with react-markdown */}
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={ChatMarkdownComponents}>
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