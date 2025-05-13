'use client';

import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Info, X } from 'lucide-react';
import { getStatusColor } from '../lib/utils';
import { AnalysisStatusMessage } from '../types/analysis';
import { useAnalysis } from '@/hooks/useAnalysis';

interface AnalysisJobDetailProps {
  jobId: string;
  jobName: string;
  jobStatus: string;
  onBack: () => void;
  onClose: () => void;
}

export default function AnalysisJobDetail({ jobId, jobName, jobStatus, onBack, onClose }: AnalysisJobDetailProps) {
  const { currentAnalysis, streamedMessages } = useAnalysis(jobId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get the messages to display - combine currentAnalysis.statusMessages with streamedMessages if currentAnalysis exists
  const messages = currentAnalysis?.jobId === jobId 
    ? [...currentAnalysis.statusMessages, ...(streamedMessages || [])].filter((msg, index, self) => 
        index === self.findIndex((m) => m.id === msg.id)
      )
    : streamedMessages || [];

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const renderMessage = (msg: AnalysisStatusMessage, index: number) => {
    const alignmentClass = 'justify-start';

    switch (msg.type) {
      case 'user_prompt':
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass}`}>
            <div className="max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm bg-purple-900/40 border border-purple-600/30 text-sm">
              <p className="text-purple-100 whitespace-pre-wrap">{msg.message}</p>
              <p className="text-xs text-purple-400/70 mt-1">
                {new Date(msg.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        );
      case 'tool_call':
        return (
          <div key={index} className={`flex ${alignmentClass} mb-2 px-3 py-1`}>
            <p className="max-w-[90%] text-[10px] text-zinc-500 font-mono">
              {msg.message}
            </p>
          </div>
        );
      case 'tool_result':
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass}`}>
            <div className="max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm bg-[#111827]/60 border border-zinc-700/50 text-sm">
              <p className="text-zinc-200 whitespace-pre-wrap">{msg.message}</p>
              <p className="text-xs text-zinc-500 mt-1">
                {new Date(msg.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        );
      case 'analysis_result':
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass}`}>
            <div className="max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm bg-blue-900/40 border border-blue-600/30 text-sm">
              <p className="text-blue-100 whitespace-pre-wrap">{msg.message}</p>
              <p className="text-xs text-blue-400/70 mt-1">
                {new Date(msg.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        );
      default:
        return (
          <div key={index} className={`mb-4 flex ${alignmentClass}`}>
            <div className="max-w-[90%] rounded-lg px-4 py-2.5 shadow-sm bg-[#111827]/60 border border-zinc-700/50 text-sm">
              <p className="text-zinc-300">
                <span className="font-medium text-zinc-500 mr-1.5">[{msg.type}]</span>
                {msg.message}
              </p>
              <p className="text-xs text-zinc-500 mt-1">
                {new Date(msg.createdAt).toLocaleString()}
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-4xl mx-4 h-[80vh] bg-gradient-to-b from-[#0a101c] to-[#050a14] rounded-lg shadow-2xl border border-zinc-800/50 overflow-hidden">
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
            <h3 className="text-lg font-semibold text-zinc-100 truncate mr-3" title={jobName}>{jobName}</h3>
            <div className={`flex items-center text-xs font-medium px-2.5 py-1 rounded-full border ${getStatusColor(jobStatus)}`}>
              {jobStatus.replace(/_/g, ' ').toUpperCase()}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="p-2 rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
              title="Job Information"
            >
              <Info size={20} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
              title="Close"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Messages container */}
        <div className="flex-grow overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700/80 scrollbar-track-transparent h-[calc(80vh-4rem)]">
          {messages.length === 0 ? (
            <div className="text-center text-zinc-500 pt-20 text-sm">
              <p>No status messages available.</p>
            </div>
          ) : (
            <div className="pt-2 px-4">
              {messages.map((msg: AnalysisStatusMessage, index: number) => renderMessage(msg, index))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}
