import { UUID } from "crypto";
import { useRun, useRunMessages } from "@/hooks/useRuns";
import { BarChart3, Zap, Clock, CheckCircle, XCircle, Loader2, Folder, Brain } from "lucide-react";
import { useState } from "react";

interface RunBoxProps {
  runId: UUID;
}

const getRunTheme = (type: 'data_integration' | 'analysis' | 'pipeline' | 'swe' | 'model_integration') => {

switch (type) {
    case 'data_integration':
    return {
        bg: 'bg-[#0E4F70]/10',
        border: 'border border-[#0E4F70]/30',
        icon: <Folder  size={12} />,
        iconColor: 'text-[#0E4F70]',
        textColor: 'text-gray-200',
        statusBg: 'bg-[#0E4F70]/15',
        statusBorder: 'border-[#0E4F70]/30',
        hover: 'hover:bg-[#0E4F70]/20 cursor-pointer',
    };
    case 'analysis':
    return {
        bg: 'bg-[#004806]/10',
        border: 'border border-[#004806]/30',
        icon: <BarChart3 size={12} />,
        iconColor: 'text-[#004806]',
        textColor: 'text-gray-200',
        statusBg: 'bg-[#004806]/15',
        statusBorder: 'border-[#004806]/30',
        hover: 'hover:bg-[#004806]/20 cursor-pointer',
    };
    case 'pipeline':
    case 'swe':
    return {
        bg: 'bg-[#840B08]/10',
        border: 'border border-[#840B08]/30',
        icon: <Zap size={12} />,
        iconColor: 'text-[#840B08]',
        textColor: 'text-gray-200',
        statusBg: 'bg-[#840B08]/15',
        statusBorder: 'border-[#840B08]/30',
        hover: 'hover:bg-[#840B08]/20 cursor-pointer',
    };
    case 'model_integration':
    return {
        bg: 'bg-[#491A32]/10',
        border: 'border border-[#491A32]/30',
        icon: <Brain size={12} />,
        iconColor: 'text-[#491A32]',
        textColor: 'text-gray-200',
        statusBg: 'bg-[#491A32]/15',
        statusBorder: 'border-[#491A32]/30',
        hover: 'hover:bg-[#491A32]/20 cursor-pointer',
    };
}
};

const getStatusInfo = (status: string) => {
switch (status) {
    case 'pending':
    return {
        icon: <Clock size={10} />,
        text: 'pending',
        color: 'text-yellow-400'
    };
    case 'running':
    return {
        icon: <Loader2 size={10} className="animate-spin" />,
        text: 'running',
        color: null
    };
    case 'completed':
    return {
        icon: <CheckCircle size={10} />,
        text: 'completed',
        color: 'text-green-600'
    };
    case 'failed':
    return {
        icon: <XCircle size={10} />,
        text: 'failed',
        color: 'text-red-600'
    };
    default:
    return {
        icon: <Clock size={10} />,
        text: 'unknown',
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
              className="text-xs text-gray-500 font-mono leading-relaxed p-1 text-[10px]"
            >
              {message.content}
            </div>
          ))}
        </div>
      )}

      {/* No messages state */}
      {(!runMessages || runMessages.length === 0) && (
        <div className="px-3 pb-2 text-xs text-gray-500 font-mono text-[10px]">
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

  const theme = getRunTheme(run.type as 'data_integration' | 'analysis' | 'pipeline' | 'swe' | 'model_integration');
  const statusInfo = getStatusInfo(run.status);

  return (
    <div className={`max-w-[80%] rounded-lg ${theme.bg} ${theme.hover} mb-2 overflow-hidden`} onClick={() => setShowMessages(!showMessages)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className={`px-2 py-0.5 rounded-md text-xs font-mono flex items-center gap-1 text-[10px]`}>
          <div className={statusInfo.color || theme.iconColor}>
            {theme.icon}
          </div>
          <span className={statusInfo.color || theme.iconColor}>
            {statusInfo.icon}
          </span>
          <span className={statusInfo.color || theme.iconColor}>
            {run.type.replace('_', ' ')} {statusInfo.text}
          </span>
        </div>

      </div>

      {/* Messages */}
      {showMessages && <RunMessageList runId={runId} />}
    </div>
  );
}