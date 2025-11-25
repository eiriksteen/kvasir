import React, { useMemo } from 'react';
import { useKvasirV1 } from '@/hooks/useKvasirV1';
import { MessageSquare } from 'lucide-react';
import { useProject } from '@/hooks/useProject';
import { useKvasirRuns } from '@/hooks/useRuns';
import { UUID } from 'crypto';
import { RunBase } from '@/types/kvasirV1';

interface ChatHistoryProps {
  onClose: () => void;
  projectId: UUID;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({
  onClose,
  projectId,
}) => {

  const { kvasirRuns } = useKvasirRuns(projectId);
  const { 
    projectRunId,
    setAgentRunId
  } = useKvasirV1(projectId);

  const { project } = useProject(projectId);

  const handleKvasirRunClick = async (kvasirRunId: UUID) => {
    try {
      await setAgentRunId(kvasirRunId);
      onClose();
    } catch (error) {
      console.error('Failed to switch kvasir run:', error);
    }
  };

  const kvasirRunsSorted = useMemo(() => {
    return kvasirRuns?.filter((run: RunBase) => 
      run.projectId === project?.id
    ).sort((a: RunBase, b: RunBase) => 
      new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()
    ) || [];
  }, [kvasirRuns, project]);

  return (
    <div className="absolute top-full right-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
      <div className="p-2">
        {kvasirRunsSorted.length === 0 && (
          <div className="text-center p-4 text-gray-500">
            <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversations yet</p>
          </div>
        )}

        {kvasirRunsSorted.length > 0 && (
          <div className="max-h-48 overflow-y-auto">
            {kvasirRunsSorted.map((run: RunBase) => (
              <button
                key={run.id}
                onClick={() => handleKvasirRunClick(run.id)}
                className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
                  projectRunId === run.id
                    ? 'bg-blue-100 text-blue-800'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <MessageSquare className="h-4 w-4 flex-shrink-0 opacity-70" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {run.runName}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 truncate">
                      {new Date(run.startedAt).toLocaleDateString()}
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