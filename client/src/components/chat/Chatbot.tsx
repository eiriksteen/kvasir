'use client';

import React, { useEffect, useRef, useState, memo } from 'react';
import { Send, Plus, History, Database, X, BarChart, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat } from '@/hooks/useChat';
import { useAgentContext } from '@/hooks/useAgentContext';
import { ChatHistory } from '@/components/chat/ChatHistory';
import { ChatMessage } from '@/types/chat';
import { TimeSeriesDataset } from '@/types/datasets';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useAnalysis } from '@/hooks/useAnalysis';

const ChatListItem = memo(({ message }: { message: ChatMessage }) => {
  const { datasets} = useDatasets();
  const { analysisJobResults } = useAnalysis();

  const hasContext = message.context && (
    message.context.datasetIds?.length > 0 || 
    message.context.analysisIds?.length > 0 || 
    message.context.automationIds?.length > 0
  );

  return (
    <div 
      className={`mb-4 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div 
        className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-md backdrop-blur-sm ${
          message.role === 'user' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-tr-none' 
            : 'bg-gray-950/40 text-white rounded-tl-none border border-gray-800/50'
        }`}
      >
        {/* Context bar */}
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
                  {datasets?.timeSeries.find((dataset: TimeSeriesDataset) => dataset.id === datasetId)?.name}
                </div>
              ))}
              
              {/* Analyses */}
              {message.context?.analysisIds?.map((analysisId: string) => (
                <div 
                  key={analysisId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-purple-900/50 text-purple-200"
                >
                  <BarChart size={10} />
                  {analysisJobResults?.analysesJobResults.find((analysis: AnalysisJobResultMetadata) => analysis.jobId === analysisId)?.name}
                </div>
              ))}
              
              {/* Automations */}
              {message.context?.automationIds?.map((automationId: string) => (
                <div 
                  key={automationId}
                  className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-orange-900/50 text-orange-200"
                >
                  <Zap size={10} />
                  Automation {automationId.slice(0, 6)}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="text-sm leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});

// Add display name to the memo component
ChatListItem.displayName = 'ChatListItem';

function Chat({ projectId }: { projectId: string }) {
  
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [showChatHistory, setShowChatHistory] = useState(false);
  
  const { submitPrompt, startNewConversation, currentConversation } = useChat(projectId);
  const { datasetsInContext, removeDatasetFromContext, analysisesInContext, removeAnalysisFromContext } = useAgentContext();
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
  }, [currentConversation?.messages]);

  const handleSubmit = () => {
    if (input.trim()) {
      submitPrompt(input);
      setInput('');
    }
  };

  const handleNewChat = async () => {
    try {
      await startNewConversation();
      setShowChatHistory(false);
    } catch (error) {
      console.error('Failed to start new conversation:', error);
    }
  };
  
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

  const handleConversationSelect = () => {
    // Close the history panel when a conversation is selected
    setShowChatHistory(false);
  };

  const isCollapsed = width <= MIN_WIDTH;

  return (
    <div 
      className="absolute right-0 h-screen text-white flex flex-col bg-gray-950/95 pt-12 border-l border-gray-800"
      style={{ width: `${width}px` }}
    >
      {/* Drag handle */}
      <div 
        ref={dragHandleRef}
        onMouseDown={handleStartDrag}
        className="absolute top-0 bottom-0 left-0 w-3 cursor-col-resize z-10 hover:bg-blue-500/10"
      >
      </div>

      {!isCollapsed && (
        <>
          {/* Header with history button */}
          <div className="border-b border-gray-800 bg-gray-900/50 p-3 flex justify-between items-center relative">
            <div className="flex-1 pl-1">
              <h3 className="text-sm font-medium text-gray-300">
                {currentConversation?.name || "Chat"}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleNewChat}
                className="p-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 text-gray-300 hover:text-white"
                title="New Chat"
              >
                <Plus size={18} />
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowChatHistory(!showChatHistory)}
                  className="p-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 text-gray-300 hover:text-white"
                  title="Chat History"
                >
                  <History size={18} />
                </button>
                <ChatHistory
                  selectedConversationId={currentConversation?.id || null}
                  onConversationSelect={handleConversationSelect}
                  projectId={projectId}
                  isOpen={showChatHistory}
                />
              </div>
            </div>
          </div>

          {/* Combined context bar */}
          <div className="border-b border-gray-800 bg-gray-900/50 p-3">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm pl-1 pt-1 font-medium text-gray-300">Context</h3>
              <h3 className="text-sm pl-1 pt-1 font-normal text-zinc-500">Select items from the left panel</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {/* {datasetsInContext.timeSeries.length === 0 && analysisesInContext.length === 0 ? (
                <h3 className="text-sm pl-1 pt-1 font-normal text-zinc-500">Select items from the left panel</h3>
              ) : ( */}
                <>
                  {/* Datasets */}
                  {datasetsInContext.timeSeries.map((dataset: TimeSeriesDataset) => (
                    <div 
                      key={dataset.id}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-blue-900/30 text-blue-300"
                    >
                      <Database size={12} />
                      {dataset.name}
                      <button 
                        onClick={() => removeDatasetFromContext(dataset)}
                        className="text-zinc-400 hover:text-white"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                  
                  {/* Analyses */}
                  {analysisesInContext.map((analysis: AnalysisJobResultMetadata) => (
                    <div 
                      key={analysis.jobId}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-purple-900/30 text-purple-300"
                    >
                      <BarChart size={12} />
                      Analysis {analysis.jobId.slice(0, 6)}
                      <button 
                        onClick={() => removeAnalysisFromContext(analysis)}
                        className="text-zinc-400 hover:text-white"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </>
              {/* )} */}
            </div>
          </div>

          {/* Quick action buttons
          <div className="border-b border-gray-800 bg-gray-900/50 p-3">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => submitPrompt("What are some interesting AI/ML or data science use cases for this data?")}
                className="px-3 py-1.5 text-sm rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Suggest use cases
              </button>
              <button
                onClick={() => submitPrompt("Who are you and what can you do?")}
                className="px-3 py-1.5 text-sm rounded-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                What can you do?
              </button>
              <button
                onClick={() => submitPrompt("Can you describe the structure and content of the selected datasets?")}
                className="px-3 py-1.5 text-sm rounded-full bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Describe my data
              </button>
              <button
                onClick={() => submitPrompt("Plan a detailed analysis on the selected datasets.")}
                className="px-3 py-1.5 text-sm rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Run analysis on datasets
              </button>
            </div>
          </div> */}

          {/* Messages container */}
          <div 
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-4 pb-24 scrollbar-thin scrollbar-thumb-gray-700"
            style={{ scrollBehavior: 'smooth' }}
          >
            {currentConversation?.messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-zinc-500">
                <div className="text-center">
                  <p className="mb-2">
                    {currentConversation?.id ? 'Start a conversation' : 'Start a new conversation'}
                  </p>
                  {!currentConversation?.id && (
                    <p className="text-sm text-zinc-600">
                      Select a conversation from history or start chatting
                    </p>
                  )}
                </div>
              </div>
            )}
            {/* Message list */}
            {currentConversation?.messages
              .sort((a: ChatMessage, b: ChatMessage) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
              .map((message: ChatMessage, index: number) => (
                <ChatListItem key={index} message={message} />
              ))}
            {/* Invisible element for scrolling to bottom */}
            <div ref={messagesEndRef} style={{ height: '1px' }} />
          </div>

          {/* Input area */}
          <div className="absolute bottom-0 left-0 right-0 bg-gray-900/90 backdrop-blur-sm p-4 border-t border-gray-800/20 z-10">
            <div className="flex rounded-full bg-gray-800/70 overflow-hidden shadow-inner">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder="Ask a question..."
                className="flex-1 bg-transparent px-4 py-3 outline-none text-white"
              />
              <button 
                onClick={handleSubmit}
                className={`px-4 transition-all duration-300 ${
                  input.trim() 
                    ? 'text-blue-400 hover:text-blue-300'
                    : 'text-zinc-500 cursor-not-allowed'
                }`}
                disabled={!input.trim()}
              >
                <Send size={20} />
              </button>
            </div>
            
            {/* Dataset indicator */}
            <div className="mt-2 flex items-center gap-2 pl-2">
              <div className="text-xs text-zinc-500 flex items-center gap-1">
                <Database size={12} />
                <span>{datasetsInContext.length} dataset{datasetsInContext.length !== 1 ? 's' : ''} in context</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function Chatbot({ projectId }: { projectId: string }) {
  const {data: session} = useSession();

  if (!session) {
    redirect("/login");
  }

  return <Chat projectId={projectId} />;
}
