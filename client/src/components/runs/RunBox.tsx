import { UUID } from "crypto";
import { useSWRConfig } from "swr"
import { useRun, useRunMessages } from "@/hooks/useRuns";
import { BarChart3, Zap, Clock, CheckCircle, XCircle, Loader2, Check, X, Network } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { useOntology } from "@/hooks/useOntology";

interface RunBoxProps {
  runId: UUID;
  projectId: UUID;
  onRunCompleteOrFail?: () => void;
}

const getRunTheme = (type: 'analysis' | 'swe' | 'extraction') => {

switch (type) {
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
    case 'extraction':
    return {
        bg: 'bg-[#083884]/10',
        border: 'border border-[#083884]/30',
        icon: <Network size={12} />,
        iconColor: 'text-[#083884]',
        textColor: 'text-gray-200',
        statusBg: 'bg-[#083884]/15',
        statusBorder: 'border-[#083884]/30',
        hover: 'hover:bg-[#083884]/20 cursor-pointer',
    };
}
};

const getStatusInfo = (status: string) => {
switch (status) {
    case 'pending':
    return {
        icon: <Clock size={10} />,
        text: 'pending',
        color: 'text-yellow-700'
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
        color: 'text-green-700'
    };
    case 'failed':
    return {
        icon: <XCircle size={10} />,
        text: 'failed',
        color: 'text-red-700'
    };
    case 'rejected':
    return {
        icon: <XCircle size={10} />,
        text: 'rejected',
        color: 'text-red-700'
    };
    default:
    return {
        icon: <Clock size={10} />,
        text: 'unknown',
        color: 'text-gray-600'
    };
    }
};

function RunMessageList({ runId, projectId }: { runId: UUID, projectId: UUID }) {
  const { runMessages } = useRunMessages(runId, projectId);

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
    </>
  );
}
  

export default function RunBox({ runId, projectId, onRunCompleteOrFail }: RunBoxProps) {
  const { run, triggerLaunchRun, triggerRejectRun } = useRun(projectId, runId);
  const { mutateDataSources, mutateDatasets, mutateModelsInstantiated, mutateAnalyses, mutatePipelines } = useOntology(projectId);
  const [isRejecting, setIsRejecting] = useState(false);
  const isPending = run?.status === 'pending';
  const [showMessages, setShowMessages] = useState(isPending);
  const [isLaunching, setIsLaunching] = useState(false);
  const { mutate } = useSWRConfig()
  const previousStatusRef = useRef<string | undefined>(run?.status);

  useEffect(() => {
    const currentStatus = run?.status;
    const previousStatus = previousStatusRef.current;
    
    // Only trigger if status changed from 'running' to 'completed' or 'failed'
    if (previousStatus === 'running' && (currentStatus === 'completed' || currentStatus === 'failed')) {
      onRunCompleteOrFail?.();
    }
    
    previousStatusRef.current = currentStatus;
  }, [run?.status, onRunCompleteOrFail]);

  if (!run) {
    return <div>Run not found</div>;
  }

  const theme = getRunTheme(run.type as 'analysis' | 'swe' | 'extraction');
  const statusInfo = getStatusInfo(run.status);



  const handleAccept = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsLaunching(true);
    try {
      await triggerLaunchRun({ runId: run.id });
    } catch (error) {
      console.error('Failed to launch run', error);
    } finally {
      setIsLaunching(false);
      if (run.type === 'swe') {
        await mutateModelsInstantiated();
      }
      else if (run.type === 'analysis') {
        await mutateAnalyses();
      }
      else if (run.type === 'extraction') {
        // Extraction runs can create/modify multiple entity types
        await mutateDataSources();
        await mutateDatasets();
        await mutateModelsInstantiated();
        await mutateAnalyses();
        await mutatePipelines();
      }
      // // Update ERD
      await mutate("projects");

    }
  };

  const handleReject = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRejecting(true);
    try {
      await triggerRejectRun({ runId: run.id });
    } catch (error) {
      console.error('Failed to reject run', error);
    } finally {
      setIsRejecting(false);
    }
  };

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

      {/* Spec and Messages */}
      {showMessages && (
        <>
          {/* Run Details */}
          <div className="px-3 pb-4 space-y-2 border-gray-700/30">
            <div className="text-xs font-mono text-gray-700">
              {run.runName}
            </div>
            <div className="text-xs text-gray-500 leading-relaxed">
              {run.description}
            </div>
            
            
            {/* Accept/Reject Buttons for Pending Runs */}
            {isPending && (
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleAccept}
                    disabled={isLaunching}
                    className="flex items-center gap-1 px-3 py-1.5 bg-green-800 hover:bg-green-600/30 border border-green-600/40 rounded text-xs text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Check size={12} />
                    {isLaunching ? 'Launching...' : 'Accept'}
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={isRejecting}
                    className="flex items-center gap-1 px-3 py-1.5 bg-red-800 hover:bg-red-600/30 border border-red-600/40 rounded text-xs text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <X size={12} />
                    {isRejecting ? 'Rejecting...' : 'Reject'}
                  </button>
              </div>
            )}
          </div>

          {/* Messages */}
          <RunMessageList runId={runId} projectId={projectId} />
        </>
      )}
    </div>
  );
}