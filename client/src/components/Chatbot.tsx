'use client';

import { memo } from 'react';
import { useState, useRef, useEffect } from 'react';
import { Send, Database, X, BarChart } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat, useConversation, useAgentContext, useAnalysis } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { ChatMessage } from '@/types/chat';
import { TimeSeriesDataset } from '@/types/datasets';
import { AnalysisJobResultMetadata } from '@/types/analysis';



interface ChatProps {
  conversationId: string;
}

const ChatListItem = memo(({ message }: { message: ChatMessage }) => {
  return (
    <div 
      className={`mb-4 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div 
        className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-md backdrop-blur-sm ${
          message.role === 'user' 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-tr-none' 
            : 'bg-blue-950/40 text-white rounded-tl-none border border-blue-800/50'
        }`}
      >
        <div className="prose prose-invert max-w-none">
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


function Chat({ conversationId }: ChatProps) {
  
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);

  const { messages, submitPrompt } = useChat(conversationId);
  const { datasetsInContext, removeDatasetFromContext, analysisesInContext, removeAnalysisFromContext } = useAgentContext();
  const { createAnalysisPlanner } = useAnalysis();
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
  }, [messages]);

  const handleSubmit = () => {
    if (input.trim()) {
      submitPrompt(input);
      setInput('');
    }
  };

  const initializeAnalysis = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    try {
      const plan = await createAnalysisPlanner();
      // Show success popup
      const popup = document.createElement('div');
      popup.style.position = 'fixed';
      popup.style.bottom = '20px';
      popup.style.right = '20px';
      popup.style.backgroundColor = '#4CAF50';
      popup.style.color = 'white';
      popup.style.padding = '15px';
      popup.style.borderRadius = '5px';
      popup.style.zIndex = '1000';
      popup.style.display = 'flex';
      popup.style.alignItems = 'center';
      popup.style.gap = '10px';

      const message = document.createElement('span');
      message.textContent = 'Analysis submitted';
      popup.appendChild(message);

      const closeButton = document.createElement('button');
      closeButton.innerHTML = '&times;';
      closeButton.style.background = 'none';
      closeButton.style.border = 'none';
      closeButton.style.color = 'white';
      closeButton.style.fontSize = '20px';
      closeButton.style.cursor = 'pointer';
      closeButton.style.padding = '0 5px';
      closeButton.onclick = () => document.body.removeChild(popup);
      popup.appendChild(closeButton);
      
      document.body.appendChild(popup);

      // Remove popup after 5 seconds if not manually closed
      const timeoutId = setTimeout(() => {
        if (document.body.contains(popup)) {
          document.body.removeChild(popup);
        }
      }, 2000);
    } catch (err) {
      setInput(err instanceof Error ? err.message : "An unknown error occurred");
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

  const isCollapsed = width <= MIN_WIDTH;

  return (
    <div 
      className="absolute right-0 h-screen pt-12 text-white flex flex-col bg-[#1a1625]/95"
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
          {/* Combined context bar */}
          <div className="border-b border-purple-900/30 bg-[#1a1625]/90 p-3">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm pl-1 pt-1 font-medium text-purple-300">Context</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {datasetsInContext.length === 0 && analysisesInContext.length === 0 ? (
                <h3 className="text-sm pl-1 pt-1 font-normal text-zinc-500">Select items from the left panel</h3>
              ) : (
                <>
                  {/* Datasets */}
                  {datasetsInContext.map((dataset: TimeSeriesDataset) => (
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
              )}
            </div>
          </div>

          {/* Quick action buttons */}
          <div className="border-b border-purple-900/30 bg-[#1a1625]/90 p-3">
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
                onClick={initializeAnalysis}
                className="px-3 py-1.5 text-sm rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                Run analysis on datasets
              </button>
            </div>
          </div>

          {/* Messages container */}
          <div 
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto p-4 pb-24 scrollbar-thin scrollbar-thumb-purple-700"
            style={{ scrollBehavior: 'smooth' }}
          >
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-zinc-500">
                <p>Start a conversation</p>
              </div>
            )}
            {/* Message list */}
            {messages.map((message, index) => (
              <ChatListItem key={index} message={message} />
            ))}
            {/* Invisible element for scrolling to bottom */}
            <div ref={messagesEndRef} style={{ height: '1px' }} />
          </div>

          {/* Input area */}
          <div className="absolute bottom-0 left-0 right-0 bg-[#1a1625]/90 backdrop-blur-sm p-4 border-t border-purple-900/20 z-10">
            <div className="flex rounded-full bg-[#2a2030]/70 overflow-hidden shadow-inner">
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


export default function Chatbot() {

  const {data: session} = useSession();
  const { currentConversationID, createConversation } = useConversation();

  if (!session) {
    redirect("/login");
  }

  useEffect(() => {
    createConversation();
  }, [createConversation]);

  if (!currentConversationID) {
    return <div>Loading...</div>;
  }

  return <Chat 
    conversationId={currentConversationID} />;
}
