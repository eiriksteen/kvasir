'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Send, Plus, History, Database, X, BarChart, Zap, Brain } from 'lucide-react';
import { useProjectChat } from '@/hooks';
import { useAgentContext } from '@/hooks/useAgentContext';
import { ChatHistory } from '@/app/projects/[projectId]/_components/chat/ChatHistory';
import { ChatMessage } from '@/types/orchestrator';
import { Dataset } from '@/types/data-objects';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { DataSource } from '@/types/data-sources';
import { UUID } from 'crypto';
import { useRunsInConversation } from '@/hooks/useRuns';
import RunBox from '@/components/runs/RunBox';
import { Run } from '@/types/runs';
import ChatMessageBox from '@/app/projects/[projectId]/_components/chat/ChatMessageBox';
import { Pipeline } from '@/types/pipeline';
import { ModelEntity } from '@/types/model';

export default function Chatbot({ projectId }: { projectId: UUID }) {
  
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [showChatHistory, setShowChatHistory] = useState(false);  

  const { submitPrompt, conversation, setProjectConversationId, conversationMessages } = useProjectChat(projectId);

  const { 
    dataSourcesInContext, 
    removeDataSourceFromContext, 
    datasetsInContext, 
    removeDatasetFromContext, 
    analysesInContext, 
    removeAnalysisFromContext,
    pipelinesInContext,
    removePipelineFromContext,
    modelEntitiesInContext,
    removeModelEntityFromContext,
  } = useAgentContext(projectId);

  const { runsInConversation } = useRunsInConversation(conversation?.id || "");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const dragHandleRef = useRef<HTMLDivElement>(null);
  
  const MIN_WIDTH = 300;
  const MAX_WIDTH = typeof window !== 'undefined' ? window.innerWidth * 0.8 : 800;


  useEffect(() => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      container.style.scrollBehavior = 'smooth';
      container.scrollTop = container.scrollHeight;
      
      const resetScrollBehavior = () => {
        container.style.scrollBehavior = 'auto';
      };
      
      const timeoutId = setTimeout(resetScrollBehavior, 500);
      
      return () => clearTimeout(timeoutId);
    }
  }, [conversationMessages, runsInConversation]);
  
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      e.preventDefault();
      
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, window.innerWidth - e.clientX));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, MIN_WIDTH, MAX_WIDTH]);

  const handleStartDrag = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleSubmitPrompt = async () => {
    setInput('');
    await submitPrompt(input);
  };

  const handleConversationSelect = () => {
    // Close the history panel when a conversation is selected
    setShowChatHistory(false);
  };

  const isCollapsed = width <= MIN_WIDTH;

  return (
    <div
      className="absolute right-0 h-screen text-gray-800 flex flex-col bg-gray-100 pt-12 border-l border-gray-200"
      style={{ width: `${width}px` }}
    >
      {/* Drag handle */}
      <div 
        ref={dragHandleRef}
        onMouseDown={handleStartDrag}
        className="absolute top-0 bottom-0 left-0 w-3 cursor-col-resize z-10 hover:bg-blue-100"
      >
      </div>

      {!isCollapsed && (
        <>
          {/* Header with history button */}
          <div className="border-b border-gray-400 p-3 flex justify-between items-center relative bg-gray-100">
            <div className="flex-1 pl-1">
              <h3 className="text-sm font-medium text-gray-900 animate-fade-in">
                {conversation?.name || "Chat"}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setProjectConversationId(null)}
                className="p-2 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-gray-600 hover:text-gray-900"
                title="New Chat"
              >
                <Plus size={18} />
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowChatHistory(!showChatHistory)}
                  className="p-2 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-gray-600 hover:text-gray-900"
                  title="Chat History"
                >
                  <History size={18} />
                </button>
                {showChatHistory && (
                  <ChatHistory
                    projectId={projectId}
                    onClose={handleConversationSelect}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Combined context bar */}
          <div className="border-b border-gray-400 p-3 bg-gray-100">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm pl-1 pt-1 font-medium text-gray-900">Context</h3>
              <h3 className="text-sm pl-1 pt-1 font-normal text-gray-600">Select items from the left panel</h3>
            </div>
            <div className="flex flex-wrap gap-2">
                <>
                  {/* Data Sources */}
                  {dataSourcesInContext.map((dataSource: DataSource) => (
                    <div
                      key={dataSource.id}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-gray-100 text-gray-700"
                    >
                      <Database size={12} />
                      {dataSource.name}
                      <button 
                        onClick={() => removeDataSourceFromContext(dataSource)}
                        className="text-[#6b7280] hover:text-gray-400"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}

                  {/* Datasets */}
                  {datasetsInContext.map((dataset: Dataset) => (
                    <div
                      key={dataset.id}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                    >
                      <Database size={12} />
                      {dataset.name}
                      <button 
                        onClick={() => removeDatasetFromContext(dataset)}
                        className="text-[#0E4F70] hover:text-gray-400"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                  
                  {/* Analyses */}
                  {analysesInContext.map((analysis: AnalysisJobResultMetadata) => (
                    <div
                      key={analysis.jobId}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#004806]/20 text-[#004806]"
                    >
                      <BarChart size={12} />
                      Analysis {analysis.jobId.slice(0, 6)}
                      <button 
                        onClick={() => removeAnalysisFromContext(analysis)}
                        className="text-[#004806] hover:text-gray-400"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}

                  {/* Pipelines */}
                  {pipelinesInContext.map((pipeline: Pipeline) => (
                    <div
                      key={pipeline.id}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#840B08]/20 text-[#840B08]"
                    >
                      <Zap size={12} />
                      {pipeline.name}
                      <button 
                        onClick={() => removePipelineFromContext(pipeline)}
                        className="text-[#840B08] hover:text-gray-400"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}

                  {/* Model Entities */}
                  {modelEntitiesInContext.map((modelEntity: ModelEntity) => (
                    <div key={modelEntity.id} className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]">
                      <Brain size={12} />
                      {modelEntity.name}
                      <button 
                        onClick={() => removeModelEntityFromContext(modelEntity)}
                        className="text-[#491A32] hover:text-gray-400"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </>
            </div>
          </div>

          {/* Messages container */}
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-4 pb-24 scrollbar-thin scrollbar-thumb-gray-700"
            style={{ scrollBehavior: 'smooth' }}
          >
            {conversationMessages.length === 0 && runsInConversation.length === 0 && (
              <div className="flex h-full items-center justify-center text-zinc-500">
                <div className="text-center">
                  <p className="mb-2">
                    {conversation?.id ? 'Start a conversation' : 'Start a new conversation'}
                  </p>
                </div>
              </div>
            )}
            
            {(() => {
              const timelineItems = [
                ...conversationMessages.map((message: ChatMessage) => ({
                  type: 'message' as const,
                  item: message,
                  createdAt: message.createdAt
                })),
                ...runsInConversation.map((run: Run) => ({
                  type: 'run' as const,
                  item: run,
                  createdAt: run.startedAt
                }))
              ];

              timelineItems.sort((a, b) => 
                new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
              );

              return timelineItems.map((timelineItem) => {
                if (timelineItem.type === 'message') {
                  return <ChatMessageBox key={`msg-${timelineItem.item.id}`} message={timelineItem.item} projectId={projectId} />;
                } else {
                  return <RunBox key={`run-${timelineItem.item.id}`} runId={timelineItem.item.id} />;
                }
              });
            })()}
            
            {/* Invisible element for scrolling to bottom */}
            <div ref={messagesEndRef} style={{ height: '1px' }} />
          </div>

          {/* Input area */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 z-10">
            <div className="flex rounded-full border border-gray-400 overflow-hidden shadow-inner" style={{ backgroundColor: '#000034' }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitPrompt()}
                placeholder="Ask a question..."
                className="flex-1 bg-transparent px-4 py-3 outline-none text-xs text-white placeholder-gray-300"
              />
              <button 
                onClick={handleSubmitPrompt}
                className={`px-4 transition-all duration-300 ${
                  input.trim()
                    ? 'text-white hover:text-gray-200'
                    : 'text-gray-400 cursor-not-allowed'
                }`}
                disabled={!input.trim()}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

