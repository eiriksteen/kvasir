import React from 'react';
import { useChat } from '@/hooks/useChat';
import { Conversation } from '@/types/chat';
import { MessageSquare, Loader2, AlertCircle } from 'lucide-react';
import { useProject } from '@/hooks/useProject';

interface ChatHistoryProps {
  selectedConversationId: string | null;
  onConversationSelect: (conversationId: string) => void;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({
  selectedConversationId,
  onConversationSelect,
}) => {
  const { 
    conversations, 
    conversationsError, 
    isLoadingConversations,
    mutateConversations,
    switchConversation
  } = useChat();

  const { selectedProject } = useProject();

  const handleConversationClick = async (conversationId: string) => {
    try {
      await switchConversation(conversationId);
      onConversationSelect(conversationId);
    } catch (error) {
      console.error('Failed to switch conversation:', error);
    }
  };

  if (isLoadingConversations) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
        <span className="ml-2 text-purple-300">Loading conversations...</span>
      </div>
    );
  }

  if (conversationsError) {
    return (
      <div className="flex items-center justify-center h-full">
        <AlertCircle className="h-6 w-6 text-red-400" />
        <span className="ml-2 text-red-400">Failed to load conversations</span>
      </div>
    );
  }

  if (!conversations || conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500">
        <MessageSquare className="h-12 w-12 mb-4" />
        <p className="text-center">No conversations yet</p>
        <p className="text-sm text-center mt-1">Start a new conversation to see it here</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-purple-900/30">
        <h2 className="text-lg font-semibold text-purple-300">Conversations</h2>
        <p className="text-sm text-zinc-500 mt-1">
          {conversations.filter((conversation: Conversation) => conversation.projectId === selectedProject?.id).length} conversation{conversations.filter((conversation: Conversation) => conversation.projectId === selectedProject?.id).length !== 1 ? 's' : ''}
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        <div className="space-y-1 p-2">
          {conversations.filter((conversation: Conversation) => conversation.projectId === selectedProject?.id).sort((a: Conversation, b: Conversation) => b.createdAt.localeCompare(a.createdAt)).map((conversation: Conversation) => (
            <button
              key={conversation.id}
              onClick={() => handleConversationClick(conversation.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors duration-200 hover:bg-purple-900/30 ${
                selectedConversationId === conversation.id
                  ? 'bg-blue-900/40 border border-blue-700/50 text-blue-300'
                  : 'text-purple-300 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-5 w-5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {conversation.name}
                  </p>
                  <p className="text-xs text-zinc-500 truncate">
                    Created at: {new Date(conversation.createdAt).toLocaleString()}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
      
      <div className="p-4 border-t border-purple-900/30">
        <button
          onClick={() => mutateConversations()}
          className="w-full px-3 py-2 text-sm text-zinc-400 hover:text-purple-300 hover:bg-purple-900/30 rounded-md transition-colors duration-200"
        >
          Refresh conversations
        </button>
      </div>
    </div>
  );
};
