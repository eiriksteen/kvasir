'use client';

import { useState, useRef, useEffect } from 'react';
import { useIntegrationAgent } from '@/hooks/useIntegrationAgent';
import { IntegrationMessage } from '@/types/data-integration';
import { Job } from '@/types/jobs';
import { getStatusColor } from '@/lib/utils';
import { Loader2, Send, Check, ThumbsDown, Wifi, WifiOff } from 'lucide-react';

interface IntegrationChatProps {
  job: Job;
}

export default function IntegrationChat({ job }: IntegrationChatProps) {
  const [userInput, setUserInput] = useState('');
  const [isDisapprovalFeedback, setIsDisapprovalFeedback] = useState(false);

  const { messages, submitFeedback, submitApproval, isConnected } = useIntegrationAgent(job.id);

  const renderMessage = (msg: IntegrationMessage, index: number) => {
    const isUserMessage = msg.type === 'feedback'; 
    const alignmentClass = isUserMessage ? 'justify-end' : 'justify-start';
    const bgColor = isUserMessage ? 'bg-blue-900/40 border-blue-600/30' : 'bg-[#111827]/60 border-zinc-700/50';

    switch (msg.type) {
      case 'tool_call':
        return (
          <div key={index} className={`flex ${alignmentClass} mb-2 px-4 py-1`}>
            <p className="max-w-[85%] text-[10px] font-mono text-gray-500">
              {msg.content}
            </p>
          </div>
        );
      case 'summary':
      case 'help_call':
        return (
           <div key={index} className={`mb-4 flex ${alignmentClass} px-4`}>
             <div className={`max-w-[85%] rounded-lg px-4 py-3 shadow-sm ${bgColor} text-sm`}>
               <p className="text-zinc-200 whitespace-pre-wrap">{msg.content}</p>
             </div>
           </div>
        );
       case 'feedback':
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass} px-4`}>
            <div className={`max-w-[85%] rounded-lg px-4 py-3 shadow-sm ${bgColor} text-sm`}>
              <p className="text-blue-100 whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        );
      default:
        return (
           <div key={index} className={`mb-4 flex ${alignmentClass} px-4`}>
             <div className={`max-w-[85%] rounded-lg px-4 py-3 shadow-sm ${bgColor} text-sm`}>
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
    if (userInput.trim() && isConnected && job.id) {
      await submitFeedback(userInput)
      setUserInput('');
      setIsDisapprovalFeedback(false);
    }
  };

  const handleDisapprove = async() => {
    setIsDisapprovalFeedback(true);
  };

  const handleApprove = async () => {
    if (job.id) {
      await submitApproval()
      setIsDisapprovalFeedback(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050a14] rounded-lg border-2 border-[#101827] shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#101827] flex-shrink-0 bg-[#0a101c] rounded-t-lg">
        <div className="flex items-center">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400 mr-4">Integration Agent Progress</h3>
          <span className="text-xs font-mono text-gray-500">{job.jobName}</span>
        </div>
        
        <div className={`flex items-center text-[10px] font-mono px-2.5 py-1 rounded-full border ${
          isConnected
            ? getStatusColor(job.status)
            : 'text-yellow-300 border-yellow-600/40 bg-yellow-900/40'
        }`}>
          {isConnected ? <Wifi size={12} className="mr-1.5" /> : <WifiOff size={12} className="mr-1.5"/>}
          {isConnected ? job.status.replace(/_/g, ' ').toUpperCase() : 'CONNECTING...'}
        </div>
      </div>

      {/* Messages container */}
      <div className="flex-grow overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700/80 scrollbar-track-transparent bg-[#050a14]">
        {messages?.length === 0 && !isConnected ? (
          <div className="flex flex-col justify-center items-center h-full text-zinc-500">
            <Loader2 size={20} className="animate-spin" />
            <p className="text-xs">Waiting for connection...</p>
          </div>
        ) : messages?.length === 0 && isConnected ? (
          <div className="text-center text-zinc-500 pt-20 text-xs">
            <p>Agent connected. Waiting for messages...</p>
          </div>
        ) : (
          <div className="pt-2">
            {messages?.map((msg, index) => renderMessage(msg, index))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input/Action Area */}
      <div className="p-3 border-t border-[#101827] bg-[#0a101c] rounded-b-lg flex-shrink-0">
        <div className="min-h-[40px] flex items-center">
          {job.status === 'awaiting_approval' && !isDisapprovalFeedback ? (
            <div className="flex items-center justify-center gap-3 w-full">
              <button
                onClick={handleApprove}
                className="flex-1 px-5 py-2 text-xs font-medium rounded-lg border border-green-600/50 bg-green-900/20 hover:bg-green-800/40 text-green-300 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                disabled={!isConnected}
              >
                <Check size={15} /> Approve
              </button>
              <button
                onClick={handleDisapprove}
                className="flex-1 px-5 py-2 text-xs font-medium rounded-lg border border-red-600/50 bg-red-900/20 hover:bg-red-800/40 text-red-300 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                disabled={!isConnected}
              >
                <ThumbsDown size={15} /> Disapprove
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
                className="flex-1 bg-transparent px-3.5 py-2.5 outline-none text-zinc-100 placeholder-zinc-500 text-xs"
                disabled={!isConnected || (job.status === 'completed' || job.status === 'failed')}
              />
              <button
                onClick={handleFeedbackSubmit}
                className={`px-3 py-1.5 transition-colors duration-200 ${userInput.trim() && isConnected ? 'text-blue-400 hover:text-blue-300' : 'text-zinc-600 cursor-not-allowed'}`}
                disabled={!userInput.trim() || !isConnected || (job.status === 'completed' || job.status === 'failed')}
              >
                <Send size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 