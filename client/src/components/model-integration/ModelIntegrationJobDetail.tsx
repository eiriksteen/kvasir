'use client';

import { useRef, useEffect } from 'react';
import { Loader2, Wifi, WifiOff, ArrowLeft } from 'lucide-react';
import { ModelIntegrationMessage } from '@/types/model-integration';
import { useModelIntegrationAgent } from '@/hooks/useModelIntegrationAgent';
import { getStatusColor } from '@/lib/utils';

interface ModelIntegrationJobDetailProps {
  integrationName: string;
  integrationStatus: string;
  onBack: () => void;
  jobId: string;
}

export default function ModelIntegrationJobDetail({ 
  integrationName, 
  integrationStatus, 
  onBack,
  jobId
}: ModelIntegrationJobDetailProps) {

  const { messages, isConnected } = useModelIntegrationAgent(jobId);

  const getStatusBadge = (status: string) => {
    const baseColor = getStatusColor(status);
    const textColor = baseColor.includes('green') ? 'text-green-300'
                     : baseColor.includes('blue') ? 'text-blue-300'
                     : baseColor.includes('yellow') ? 'text-yellow-300'
                     : baseColor.includes('red') ? 'text-red-300'
                     : 'text-zinc-300';
    const bgColor = baseColor.includes('green') ? 'bg-green-900/30 border-green-700/50'
                    : baseColor.includes('blue') ? 'bg-blue-900/30 border-blue-700/50'
                    : baseColor.includes('yellow') ? 'bg-yellow-900/30 border-yellow-700/50'
                    : baseColor.includes('red') ? 'bg-red-900/30 border-red-700/50'
                    : 'bg-zinc-700/30 border-zinc-600/50';

    return {
      textColor,
      bgColor
    };
  };

  const renderMessage = (msg: ModelIntegrationMessage, index: number) => {
    const alignmentClass = 'justify-start'; // Always align left
    let textColorClass = 'text-zinc-500'; // Default color
    
    if (msg.content.toLowerCase().includes('fail')) {
      textColorClass = 'text-red-400';
    } else if (msg.type === 'result') {
      textColorClass = 'text-green-400';
    }

      return (
        <div key={index} className={`flex ${alignmentClass} mb-2 px-3 py-1`}>
          <p className={`max-w-[90%] text-[10px] ${textColorClass} font-mono`}>
            {msg.content}
          </p>
        </div>
      );
  };

  // Scroll to bottom when messages update
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


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
                     ? (() => {
                         const badge = getStatusBadge(integrationStatus);
                         return `${badge.textColor} ${badge.bgColor}`;
                       })()
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
    </div>
  );
} 