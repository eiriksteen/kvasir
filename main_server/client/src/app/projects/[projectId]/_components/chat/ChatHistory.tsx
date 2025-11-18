import React from 'react';
import { useProjectChat } from '@/hooks/useProjectChat';
import { Conversation } from '@/types/api/orchestrator';
import { MessageSquare, Loader2, AlertCircle } from 'lucide-react';
import { useProject } from '@/hooks/useProject';
import { useConversations } from '@/hooks/useConversations';
import { UUID } from 'crypto';

interface ChatHistoryProps {
  onClose: () => void;
  projectId: UUID;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({
  onClose,
  projectId,
}) => {

  const { conversations, isLoading, isError } = useConversations(projectId);
  
  const { 
    conversation,
    setProjectConversationId
  } = useProjectChat(projectId);

  const { project } = useProject(projectId);

  const handleConversationClick = async (conversationId: UUID) => {
    try {
      await setProjectConversationId(conversationId);
      onClose();
    } catch (error) {
      console.error('Failed to switch conversation:', error);
    }
  };

  const projectConversations = conversations?.filter((conversation: Conversation) => 
    conversation.projectId === project?.id
  ).sort((a: Conversation, b: Conversation) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  ) || [];

  return (
    <div className="absolute top-full right-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
      <div className="p-2">
        {isLoading && (
          <div className="flex items-center justify-center p-4">
            <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
            <span className="ml-2 text-gray-600 text-sm">Loading...</span>
          </div>
        )}

        {isError && (
          <div className="flex items-center justify-center p-4">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="ml-2 text-red-500 text-sm">Failed to load</span>
          </div>
        )}

        {!isLoading && !isError && projectConversations.length === 0 && (
          <div className="text-center p-4 text-gray-500">
            <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversations yet</p>
          </div>
        )}

        {!isLoading && !isError && projectConversations.length > 0 && (
          <div className="max-h-48 overflow-y-auto">
            {projectConversations.map((projectConversation: Conversation) => (
              <button
                key={projectConversation.id}
                onClick={() => handleConversationClick(projectConversation.id)}
                className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                  conversation?.id === projectConversation.id
                    ? 'bg-blue-100 text-blue-800'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <MessageSquare className="h-4 w-4 flex-shrink-0 opacity-70" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {projectConversation.name}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 truncate">
                      {new Date(projectConversation.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};