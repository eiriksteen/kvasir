'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Database, X } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';

// Message type
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatbotProps {
  selectedDatasets: TimeSeriesDataset[];
  onRemoveDataset: (datasetId: string) => void;
}

export default function Chatbot({ selectedDatasets = [], onRemoveDataset }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [width, setWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [contextDatasets, setContextDatasets] = useState<TimeSeriesDataset[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dragHandleRef = useRef<HTMLDivElement>(null);
  
  // Width constraints
  const MIN_WIDTH = 300;
  const MAX_WIDTH = typeof window !== 'undefined' ? window.innerWidth * 0.8 : 800;

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update context datasets when selectedDatasets changes
  useEffect(() => {
    setContextDatasets(selectedDatasets);
  }, [selectedDatasets]);

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

  const handleSendMessage = () => {
    if (input.trim() === '') return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    setInput('');
    
    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm your AI assistant. How can I help you today?",
        sender: 'ai',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleStartDrag = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const removeDatasetFromContext = (datasetId: string) => {
    onRemoveDataset(datasetId);
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
                {contextDatasets.length > 0 ? (
                  contextDatasets.map(dataset => (
                    <div 
                      key={dataset.id}
                    className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-blue-900/30 text-blue-300"
                  >
                    {dataset.name}
                    <button 
                      onClick={() => removeDatasetFromContext(dataset.id)}
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
          <div className="flex-1 overflow-y-auto p-4 pb-20 scrollbar-thin scrollbar-thumb-purple-700">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-zinc-500">
                <p>Start a conversation</p>
              </div>
            )}

            {/* Message list */}
            {messages.map(message => (
              <div 
                key={message.id} 
                className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-md backdrop-blur-sm ${
                    message.sender === 'user' 
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-tr-none' 
                      : 'bg-blue-950/40 text-white rounded-tl-none border border-blue-800/50'
                  }`}
                >
                  {message.content}
                  <div className={`text-xs mt-1 ${message.sender === 'user' ? 'text-blue-200' : 'text-zinc-400'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="absolute bottom-0 left-0 right-0 bg-[#1a1625]/90 backdrop-blur-sm p-4 border-t border-purple-900/20">
            <div className="flex rounded-full bg-[#2a2030]/70 overflow-hidden shadow-inner">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask a question..."
                className="flex-1 bg-transparent px-4 py-3 outline-none text-white"
              />
              <button 
                onClick={handleSendMessage} 
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
                <span>{contextDatasets.length} dataset{contextDatasets.length !== 1 ? 's' : ''} in context</span>
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
}
