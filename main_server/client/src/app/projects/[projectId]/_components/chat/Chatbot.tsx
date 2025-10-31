'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Send, Plus, History, Database, X, BarChart, Zap, Brain, Folder, ChevronLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { useProjectChat } from '@/hooks';
import { useAgentContext } from '@/hooks/useAgentContext';
import { useDataSources, useDatasets, usePipelines, useModelEntities, useAnalyses } from '@/hooks';
import { ChatHistory } from '@/app/projects/[projectId]/_components/chat/ChatHistory';
import { ChatMessage } from '@/types/orchestrator';
import { UUID } from 'crypto';
import { useRunsInConversation } from '@/hooks/useRuns';
import RunBox from '@/components/runs/RunBox';
import { Run } from '@/types/runs';
import ChatMessageBox from '@/app/projects/[projectId]/_components/chat/ChatMessageBox';
import { DataSource } from '@/types/data-sources';
import { Dataset } from '@/types/data-objects';
import { Pipeline } from '@/types/pipeline';
import { ModelEntity } from '@/types/model';
import { AnalysisSmall } from '@/types/analysis';

export default function Chatbot({ projectId }: { projectId: UUID }) {
  
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [showAllContext, setShowAllContext] = useState(false);

  const { submitPrompt, conversation, setProjectConversationId, conversationMessages, continueConversation } = useProjectChat(projectId);

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

  // Get the actual objects to display names
  const { dataSources } = useDataSources(projectId);
  const { datasets } = useDatasets(projectId);
  const { pipelines } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalyses(projectId);

  const { runsInConversation } = useRunsInConversation(conversation?.id || "");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const dragHandleRef = useRef<HTMLDivElement>(null);
  
  // Constants for resizing behavior
  const DEFAULT_WIDTH = 400;  
  const MIN_WIDTH = 150;
  const COLLAPSE_THRESHOLD = 100;
  const COLLAPSED_WIDTH = 40;
  const MAX_WIDTH = typeof window !== 'undefined' ? window.innerWidth * 0.8 : 800;

  // Auto-scroll to bottom when messages change
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
      
      let newWidth = window.innerWidth - e.clientX;
      
      // Auto-collapse immediately when dragged below threshold
      if (newWidth < COLLAPSE_THRESHOLD) {
        newWidth = COLLAPSED_WIDTH;
      } else {
        newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
      }
      
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
  }, [isDragging, MIN_WIDTH, MAX_WIDTH, COLLAPSE_THRESHOLD, COLLAPSED_WIDTH]);

  const handleStartDrag = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleSubmitPrompt = async () => {
    setInput('');
    await submitPrompt(input);
  };

  const handleConversationSelect = () => {
    // Close the history panel and expand chat when a conversation is selected
    setShowChatHistory(false);
    if (isCollapsed) {
      handleExpandChat();
    }
  };

  const handleRunCompleteOrFail = () => {
    if (!conversation?.id) return;
    continueConversation(conversation.id);
  };

  const handleExpandChat = () => {
    setWidth(DEFAULT_WIDTH);
  };

  const isCollapsed = width <= COLLAPSED_WIDTH;

  // Keyboard shortcut for CMD + i to toggle chatbot
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'i') {
        event.preventDefault();
        if (isCollapsed) {
          handleExpandChat();
        } else {
          setWidth(COLLAPSED_WIDTH);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isCollapsed]);

  // Helper functions to get context items with names
  const getDataSourcesInContext = () => {
    if (!dataSources) return [];
    return dataSourcesInContext
      .map((id: UUID) => dataSources.find((ds: DataSource) => ds.id === id))
      .filter((ds: DataSource | undefined): ds is DataSource => ds !== undefined);
  };

  const getDatasetsInContext = () => {
    if (!datasets) return [];
    return datasetsInContext
      .map((id: UUID) => datasets.find((ds: Dataset) => ds.id === id))
      .filter((ds: Dataset | undefined): ds is Dataset => ds !== undefined);
  };

  const getPipelinesInContext = () => {
    if (!pipelines) return [];
    return pipelinesInContext
      .map((id: UUID) => pipelines.find((p: Pipeline) => p.id === id))
      .filter((p: Pipeline | undefined): p is Pipeline => p !== undefined);
  };

  const getModelEntitiesInContext = () => {
    if (!modelEntities) return [];
    return modelEntitiesInContext
      .map((id: UUID) => modelEntities.find((m: ModelEntity) => m.id === id))
      .filter((m: ModelEntity | undefined): m is ModelEntity => m !== undefined);
  };

  const getAnalysesInContext = () => {
    if (!analysisObjects) return [];
    return analysesInContext
      .map((id: UUID) => analysisObjects.find((a: AnalysisSmall) => a.id === id))
      .filter((a: AnalysisSmall | undefined): a is AnalysisSmall => a !== undefined);
  };

  // Context item configuration
  const contextItemConfigs = [
    { items: getDataSourcesInContext(), type: 'dataSource', iconName: 'Database', bgColor: 'bg-gray-200', textColor: 'text-gray-600', removeFn: (item: DataSource) => removeDataSourceFromContext(item.id) },
    { items: getDatasetsInContext(), type: 'dataset', iconName: 'Folder', bgColor: 'bg-[#0E4F70]/20', textColor: 'text-[#0E4F70]', removeFn: (item: Dataset) => removeDatasetFromContext(item.id) },
    { items: getAnalysesInContext(), type: 'analysis', iconName: 'BarChart', bgColor: 'bg-[#004806]/20', textColor: 'text-[#004806]', removeFn: (item: AnalysisSmall) => removeAnalysisFromContext(item.id) },
    { items: getPipelinesInContext(), type: 'pipeline', iconName: 'Zap', bgColor: 'bg-[#840B08]/20', textColor: 'text-[#840B08]', removeFn: (item: Pipeline) => removePipelineFromContext(item.id) },
    { items: getModelEntitiesInContext(), type: 'modelEntity', iconName: 'Brain', bgColor: 'bg-[#491A32]/20', textColor: 'text-[#491A32]', removeFn: (item: ModelEntity) => removeModelEntityFromContext(item.id) }
  ];

  // Helper function to get all context items
  const getAllContextItems = () => {
    return contextItemConfigs.flatMap(config => 
      config.items.map((item: unknown) => ({ ...config, item }))
    );
  };

  // Icon mapping for context items
  const iconMap = {
    Database: Database,
    Folder: Folder,
    BarChart: BarChart,
    Zap: Zap,
    Brain: Brain
  };

  const renderIcon = (iconName: string, size: number) => {
    const IconComponent = iconMap[iconName as keyof typeof iconMap] || Database;
    return <IconComponent size={size} />;
  };

  const allContextItems = getAllContextItems();
  const totalContextCount = allContextItems.length;
  const remainingCount = totalContextCount - 1;

  // Render collapsed chat view
  const renderCollapsedView = () => (
    <div className="flex flex-col h-full">
      {/* History button at top */}
      <div className="flex items-center justify-center h-9 border-b border-t border-gray-400 bg-gray-100">
        <div className="relative">
          <button
            onClick={() => {
              setShowChatHistory(!showChatHistory);
              if (!showChatHistory) {
                handleExpandChat();
              }
            }}
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

      {/* Plus button below */}
      <div className="flex items-center justify-center pt-2">
        <button
          onClick={() => {
            setProjectConversationId(null);
            handleExpandChat();
          }}
          className="p-2 rounded-lg hover:bg-gray-300 transition-colors duration-200 text-gray-600 hover:text-gray-900"
          title="New Chat"
        >
          <Plus size={18} />
        </button>
      </div>

      {/* Expand button at bottom */}
      <div className="flex-1"></div>
      <div className="flex items-center justify-center px-3 py-2">
        <button
          onClick={handleExpandChat}
          className="p-2 rounded-full text-white hover:bg-[#000066] border border-gray-400 bg-[#000034]"
          title="Expand chat"
        >
          <ChevronLeft size={14} />
        </button>
      </div>
    </div>
  );

  // Render context bar
  const renderContextBar = () => (
    <div className="border-b border-gray-400 bg-gray-100">
      {/* Fixed header row - never moves */}
      <div className="h-9 flex items-center px-3 gap-3">
        <h3 className="text-xs font-mono text-gray-900 whitespace-nowrap flex-shrink-0">Context</h3>
        <div className="flex items-center gap-2 flex-1">
          {totalContextCount !== 0 && (
            <>
              {/* Show context items in header row ONLY when collapsed */}
              {!showAllContext && allContextItems.length > 0 && (
                <div
                  className={`px-2 py-1 text-xs rounded-full flex items-center gap-1 ${allContextItems[0].bgColor} ${allContextItems[0].textColor} flex-shrink-0`}
                >
                  {renderIcon(allContextItems[0].iconName, 12)}
                  <span className="truncate max-w-[150px]">{allContextItems[0].item.name}</span>
                  <button
                    onClick={() => allContextItems[0].removeFn(allContextItems[0].item)}
                    className={`${allContextItems[0].textColor} hover:text-gray-400 flex-shrink-0`}
                  >
                    <X size={12} />
                  </button>
                </div>
              )}

              {/* Show (X more) indicator when collapsed and there are items that don't fit */}
              {!showAllContext && remainingCount > 0 && (
                <span className="text-xs text-gray-500 flex-shrink-0">
                  ({remainingCount} more)
                </span>
              )}

              {/* Toggle button - only show if there are more than 1 items */}
              {totalContextCount > 1 && (
                <button
                  onClick={() => setShowAllContext(!showAllContext)}
                  className="p-1 rounded hover:bg-gray-200 transition-colors duration-200 text-gray-600 hover:text-gray-900 flex-shrink-0"
                  title={showAllContext ? "Show less" : "Show all"}
                >
                  {showAllContext ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* All items displayed in rows under header when expanded */}
      {showAllContext && (
        <div className="px-3 pb-3">
          <div className="grid grid-cols-2 gap-2 w-full">
            {allContextItems.map((contextItem) => (
              <div
                key={`${contextItem.type}-${contextItem.item.id}`}
                className={`px-2 py-1 text-xs rounded-full flex items-center gap-1 ${contextItem.bgColor} ${contextItem.textColor} flex-shrink-0`}
              >
                {renderIcon(contextItem.iconName, 12)}
                <span className="truncate flex-1">{contextItem.item.name}</span>
                <button
                  onClick={() => contextItem.removeFn(contextItem.item)}
                  className={`${contextItem.textColor} hover:text-gray-400 flex-shrink-0`}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Render timeline of messages and runs
  const renderTimeline = () => {
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
        return (
          <ChatMessageBox 
            key={`msg-${timelineItem.item.id}`} 
            message={timelineItem.item} 
            projectId={projectId} 
          />
        );
      } else {
        return (
          <RunBox 
            key={`run-${timelineItem.item.id}`} 
            runId={timelineItem.item.id} 
            projectId={projectId} 
            onRunCompleteOrFail={handleRunCompleteOrFail}
          />
        );
      }
    });
  };

  return (
    <div
      className="h-full text-gray-800 flex flex-col bg-gray-100 border-l border-gray-200 pt-12 flex-shrink-0 relative"
      style={{ width: `${width}px` }}
    >
      {/* Drag handle */}
      <div 
        ref={dragHandleRef}
        onMouseDown={handleStartDrag}
        className="absolute top-0 bottom-0 left-0 w-2 cursor-col-resize z-10 hover:bg-gray-300 transition-colors"
      >
      </div>

      {isCollapsed ? renderCollapsedView() : (
        <>
          {/* Header with history button */}
          <div className="border-b border-t border-gray-400 h-9 flex justify-between items-center relative bg-gray-100 px-3">
            <div className="flex-1">
              <h3 className="text-xs font-mono text-gray-900">
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

          {/* Context bar */}
          {renderContextBar()}


          {/* Messages container */}
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto px-3 py-3 pb-24 scrollbar-thin scrollbar-thumb-gray-700"
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
            
            {renderTimeline()}
            
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