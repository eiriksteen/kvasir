'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Database, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useChat, useCreateConversation, useUpdateContext } from '@/hooks/apiHooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';


interface ChatbotProps {
  datasetsInContext: TimeSeriesDataset[];
  automationsInContext: Automation[];
  onRemoveDatasetFromContext: (datasetId: string) => void;
  onRemoveAutomationFromContext: (automationId: string) => void;
}

interface ChatProps extends ChatbotProps {
  conversationId: string;
  token: string;
}

function Chat({ datasetsInContext, automationsInContext, onRemoveDatasetFromContext, onRemoveAutomationFromContext, conversationId, token }: ChatProps) {
  
  const [prompt, setPrompt] = useState('');
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);

  const { response, messages } = useChat(prompt, token, conversationId);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dragHandleRef = useRef<HTMLDivElement>(null);
  
  // Width constraints
  const MIN_WIDTH = 300;
  const MAX_WIDTH = typeof window !== 'undefined' ? window.innerWidth * 0.8 : 800;

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, response]);

  // Handle message submission
  const handleSubmit = () => {
    if (input.trim()) {
      setPrompt(input);
      setInput(''); // Clear input after submission
    }
  };

  // Handle resize
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
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // Touch handlers for mobile
  useEffect(() => {
    const dragHandle = dragHandleRef.current;
    
    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, window.innerWidth - e.touches[0].clientX));
      setWidth(newWidth);
    };

    if (dragHandle) {
      dragHandle.addEventListener('touchmove', handleTouchMove, { passive: false });
    }

    return () => {
      if (dragHandle) {
        dragHandle.removeEventListener('touchmove', handleTouchMove);
      }
    };
  }, []);

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
          
          {/* Dataset context panel - only shown when datasets are available */}
            <div className="border-b border-purple-900/30 bg-[#1a1625]/90 p-3">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm pl-1 pt-1 font-medium text-purple-300">Selected Datasets</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {datasetsInContext.length > 0 ? (
                  datasetsInContext.map(dataset => (
                    <div 
                      key={dataset.id}
                      className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-blue-900/30 text-blue-300"
                    >
                      {dataset.name}
                      <button 
                        onClick={() => onRemoveDatasetFromContext(dataset.id)}
                      className="text-zinc-400 hover:text-white"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))
                ) : ( <h3 className="text-sm pl-1 pt-1 font-normal text-zinc-500">Select datasets from the left panel</h3>
                )}
              </div>
            </div>

          {/* Messages container */}
          <div className="flex-1 overflow-y-auto p-4 pb-24 scrollbar-thin scrollbar-thumb-purple-700">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-zinc-500">
                <p>Start a conversation</p>
              </div>
            )}

            {/* Message list */}
            {messages.map(message => (
              <div 
                key={message.content} 
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
            ))}
            {response && (
            <div 
              key={response} 
              className={`mb-4 flex ${'justify-start'}`}>
              <div 
                className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-md backdrop-blur-sm ${
                  'bg-blue-950/40 text-white rounded-tl-none border border-blue-800/50'
                }`}
              >
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {response}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
            )}
            <div ref={messagesEndRef} />
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

export default function Chatbot({ datasetsInContext, automationsInContext, onRemoveDatasetFromContext, onRemoveAutomationFromContext }: ChatbotProps) {

  const [conversationId, setConversationId] = useState<string | null>(null);
  const {data: session} = useSession();

  if (!session) {
    redirect("/login");
  }

  useCreateConversation(setConversationId);
  useUpdateContext(conversationId, datasetsInContext, automationsInContext);

  if (!conversationId) {
    return <div>Loading...</div>;
  }

  return <Chat 
    datasetsInContext={datasetsInContext} 
    automationsInContext={automationsInContext} 
    onRemoveDatasetFromContext={onRemoveDatasetFromContext} 
    onRemoveAutomationFromContext={onRemoveAutomationFromContext} 
    conversationId={conversationId} 
    token={session?.APIToken.accessToken}  />;
}