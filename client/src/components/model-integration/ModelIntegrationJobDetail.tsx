'use client';

import { useState, useRef, useEffect } from 'react';
import { Loader2, Wifi, WifiOff, ArrowLeft, Send, Check, ThumbsDown } from 'lucide-react';

interface ModelIntegrationJobDetailProps {
  integrationName: string;
  integrationStatus: string;
  onBack: () => void;
}

interface ModelIntegrationMessage {
  type: 'tool_call' | 'summary' | 'help_call' | 'feedback' | 'info';
  content: string;
}

export default function ModelIntegrationJobDetail({ 
  integrationName, 
  integrationStatus, 
  onBack 
}: ModelIntegrationJobDetailProps) {
  const [messages, setMessages] = useState<ModelIntegrationMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isDisapprovalFeedback, setIsDisapprovalFeedback] = useState(false);
  const [isConnected] = useState(true); // Mock connection state

  const renderMessage = (msg: ModelIntegrationMessage, index: number) => {
    const isUserMessage = msg.type === 'feedback'; 
    const alignmentClass = isUserMessage ? 'justify-end' : 'justify-start';
    const bgColor = isUserMessage ? 'bg-blue-900/40 border-blue-600/30' : 'bg-[#111827]/60 border-zinc-700/50';

    switch (msg.type) {
      case 'tool_call':
        return (
          <div key={index} className={`flex ${alignmentClass} mb-2 px-3 py-1`}>
            <p className="max-w-[90%] text-[10px] text-zinc-500 font-mono">
              {msg.content}
            </p>
          </div>
        );
      case 'summary':
      case 'help_call':
        return (
           <div key={index} className={`mb-4 flex ${alignmentClass}`}>
             <div className={`max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm ${bgColor} text-sm`}>
               <p className="text-zinc-200 whitespace-pre-wrap">{msg.content}</p>
             </div>
           </div>
        );
       case 'feedback':
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass}`}>
            <div className={`max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm ${bgColor} text-sm`}>
              <p className="text-blue-100 whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        );
      default:
        return (
           <div key={index} className={`mb-4 flex ${alignmentClass}`}>
             <div className={`max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm ${bgColor} text-sm`}>
                <p className="text-zinc-300"><span className="font-medium text-zinc-500 mr-1.5">[{msg.type}]</span>{msg.content}</p>
             </div>
           </div>
        );
    }
  };

  // Scroll to bottom when messages update
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFeedbackSubmit = async () => {
    if (userInput.trim() && isConnected) {
      // Mock feedback submission
      const newMessage: ModelIntegrationMessage = {
        type: 'feedback',
        content: userInput
      };
      setMessages(prev => [...prev, newMessage]);
      setUserInput('');
      setIsDisapprovalFeedback(false);
    }
  };

  const handleDisapprove = async() => {
    setIsDisapprovalFeedback(true);
  };

  const handleApprove = async () => {
    // Mock approval
    const newMessage: ModelIntegrationMessage = {
      type: 'info',
      content: 'Model integration approved successfully!'
    };
    setMessages(prev => [...prev, newMessage]);
    setIsDisapprovalFeedback(false);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-[#0a101c] to-[#050a14]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#1f2937] flex-shrink-0 bg-[#0a101c]/70 backdrop-blur-sm">
        <div className="flex items-center">
            <button
              onClick={onBack}
              className="mr-4 p-2 rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors flex items-center text-sm"
            >
                <ArrowLeft size={16} className="mr-1.5"/>
                Back
            </button>
             <h3 className="text-lg font-semibold text-zinc-100 truncate mr-3" title={integrationName}>{integrationName}</h3>
             <div className={`flex items-center text-xs font-medium px-2.5 py-1 rounded-full border ${
                 isConnected
                     ? 'text-green-300 border-green-600/40 bg-green-900/40'
                     : 'text-yellow-300 border-yellow-600/40 bg-yellow-900/40'
                 }`}>
              {isConnected ? <Wifi size={13} className="mr-1.5" /> : <WifiOff size={13} className="mr-1.5"/>}
               {isConnected ? integrationStatus.replace(/_/g, ' ').toUpperCase() : 'CONNECTING...'}
            </div>
        </div>
      </div>

      {/* Messages container */}
      <div className="flex-grow overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700/80 scrollbar-track-transparent">
        {messages?.length === 0 && !isConnected && (
            <div className="flex flex-col justify-center items-center h-full text-zinc-500">
                 <Loader2 size={24} className="animate-spin" />
                 <p>Waiting for connection...</p>
            </div>
        )}
         {messages?.length === 0 && isConnected && (
            <div className="text-center text-zinc-500 pt-20 text-sm">
                 <p>Agent connected. Waiting for messages...</p>
            </div>
        )}
        <div className="pt-2">
          {messages?.map((msg, index) => renderMessage(msg, index))}
        </div>
         <div ref={messagesEndRef} />
      </div>

      {/* Input/Action Area */}
      <div className="p-3 border-t border-[#1f2937] bg-[#0a101c]/90 backdrop-blur-sm flex-shrink-0">
        <div className="min-h-[40px] flex items-center">
          {integrationStatus === 'awaiting_approval' && !isDisapprovalFeedback ? (
            <div className="flex items-center justify-center gap-3 w-full">
              <button
                onClick={handleApprove}
                className="flex-1 px-5 py-2 text-sm font-medium rounded-lg border border-green-600/50 bg-green-900/20 hover:bg-green-800/40 text-green-300 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                disabled={!isConnected}
              >
                <Check size={17} /> Approve
              </button>
              <button
                onClick={handleDisapprove}
                className="flex-1 px-5 py-2 text-sm font-medium rounded-lg border border-red-600/50 bg-red-900/20 hover:bg-red-800/40 text-red-300 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                disabled={!isConnected}
              >
                <ThumbsDown size={17} /> Disapprove
              </button>
            </div>
          ) : (
            <div className="flex rounded-lg bg-[#111827]/80 border border-zinc-700/80 overflow-hidden shadow-inner items-center focus-within:ring-2 focus-within:ring-blue-600 focus-within:border-transparent w-full">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleFeedbackSubmit()}
                placeholder={isDisapprovalFeedback ? "What should the agent change?" : "Send feedback or message..."}
                className="flex-1 bg-transparent px-3.5 py-2.5 outline-none text-zinc-100 placeholder-zinc-500 text-sm"
                disabled={!isConnected || integrationStatus === 'completed' || integrationStatus === 'failed'}
              />
              <button
                onClick={handleFeedbackSubmit}
                className={`px-3 py-1.5 transition-colors duration-200 ${userInput.trim() && isConnected ? 'text-blue-400 hover:text-blue-300' : 'text-zinc-600 cursor-not-allowed'}`}
                disabled={!userInput.trim() || !isConnected || integrationStatus === 'completed' || integrationStatus === 'failed'}
              >
                <Send size={18} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 