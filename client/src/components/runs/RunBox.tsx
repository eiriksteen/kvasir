import { UUID } from "crypto";
import { useRun, useRunMessages } from "@/hooks/useRuns";
import { BarChart3, Zap, Clock, CheckCircle, XCircle, Loader2, Folder } from "lucide-react";
import { useState } from "react";

interface RunBoxProps {
  runId: UUID;
}

const getRunTheme = (type: 'data_integration' | 'analysis' | 'automation') => {
switch (type) {
    case 'data_integration':
    return {
        bg: 'bg-blue-500/5',
        border: 'border border-blue-400/30',
        icon: <Folder  size={12} />,
        iconColor: 'text-blue-400',
        textColor: 'text-gray-200',
        statusBg: 'bg-blue-500/15',
        statusBorder: 'border-blue-400/30',
        hover: 'hover:bg-blue-500/10 cursor-pointer',
    };
    case 'analysis':
    return {
        bg: 'bg-purple-500/5',
        border: 'border border-purple-400/30',
        icon: <BarChart3 size={12} />,
        iconColor: 'text-purple-400',
        textColor: 'text-gray-200',
        statusBg: 'bg-purple-500/15',
        statusBorder: 'border-purple-400/30',
        hover: 'hover:bg-purple-500/10 cursor-pointer',
    };
    case 'automation':
    return {
        bg: 'bg-orange-500/5',
        border: 'border border-orange-400/30',
        icon: <Zap size={12} />,
        iconColor: 'text-orange-400',
        textColor: 'text-gray-200',
        statusBg: 'bg-orange-500/15',
        statusBorder: 'border-orange-400/30',
        hover: 'hover:bg-orange-500/10 cursor-pointer',
    };
}
};

const getStatusInfo = (status: string) => {
switch (status) {
    case 'pending':
    return {
        icon: <Clock size={10} />,
        text: 'Pending',
        color: 'text-yellow-400'
    };
    case 'running':
    return {
        icon: <Loader2 size={10} className="animate-spin" />,
        text: 'Running',
        color: 'text-blue-400'
    };
    case 'completed':
    return {
        icon: <CheckCircle size={10} />,
        text: 'Completed',
        color: 'text-green-400'
    };
    case 'failed':
    return {
        icon: <XCircle size={10} />,
        text: 'Failed',
        color: 'text-red-400'
    };
    default:
    return {
        icon: <Clock size={10} />,
        text: 'Unknown',
        color: 'text-gray-400'
    };
    }
};

function RunMessageList({ runId }: { runId: UUID }) {
  const { runMessages } = useRunMessages(runId);

  return (
    <>
      {/* Messages */}
      {runMessages && runMessages.length > 0 && (
        <div className="px-3 pb-2 space-y-1">
          {runMessages.map((message) => (
            <div 
              key={message.id}
              className="text-xs text-gray-500 font-mono leading-relaxed p-1"
            >
              {message.content}
            </div>
          ))}
        </div>
      )}

      {/* No messages state */}
      {(!runMessages || runMessages.length === 0) && (
        <div className="px-3 pb-2 text-xs text-gray-500 font-mono">
          No messages yet
        </div>
      )}
    </>
  );
}
  

export default function RunBox({ runId }: RunBoxProps) {
  const { run } = useRun(runId);
  const [showMessages, setShowMessages] = useState(false);

  if (!run) {
    return <div>Run not found</div>;
  }

  const theme = getRunTheme(run.type);
  const statusInfo = getStatusInfo(run.status);

  return (
    <div className={`max-w-[80%] rounded-lg ${theme.bg} ${theme.hover} mb-2 overflow-hidden`} onClick={() => setShowMessages(!showMessages)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className={`px-2 py-0.5 rounded-md text-xs font-mono flex items-center gap-1`}>
          <div className={statusInfo.color}>
            {theme.icon}
          </div>
          <span className={statusInfo.color}>
            {statusInfo.icon}
          </span>
          <span className={statusInfo.color}>
            {statusInfo.text} {run.type.replace('_', ' ')}
          </span>
        </div>

      </div>

      {/* Messages */}
      {showMessages && <RunMessageList runId={runId} />}
    </div>
  );
}