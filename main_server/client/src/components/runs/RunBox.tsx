import { UUID } from "crypto";
import { useRun, useRunMessages } from "@/hooks/useRuns";
import { BarChart3, Zap, Clock, CheckCircle, XCircle, Loader2, Folder, Brain, Check, X, Database } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { useDatasets } from "@/hooks/useDatasets";
import { useProjectDataSources } from "@/hooks/useDataSources";
import { useModelEntities } from "@/hooks/useModelEntities";
import { usePipelines } from "@/hooks/usePipelines";
import { Dataset } from "@/types/data-objects";
import { DataSource } from "@/types/data-sources";
import { ModelEntity } from "@/types/model";
import { Pipeline } from "@/types/pipeline";

interface RunBoxProps {
  runId: UUID;
  projectId: UUID;
  onRunCompleteOrFail?: () => void;
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

    </>
  );
}
  

export default function RunBox({ runId, projectId, onRunCompleteOrFail }: RunBoxProps) {
  const { run, triggerLaunchRun, triggerRejectRun } = useRun(runId);
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useProjectDataSources(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { pipelines } = usePipelines(projectId);
  const [isRejecting, setIsRejecting] = useState(false);
  const isPending = run?.status === 'pending';
  const [showMessages, setShowMessages] = useState(isPending);
  const [isLaunching, setIsLaunching] = useState(false);
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

  const theme = getRunTheme(run.type as 'data_integration' | 'analysis' | 'pipeline' | 'swe' | 'model_integration');
  const statusInfo = getStatusInfo(run.status);
  
  const hasInputs = run.inputs && (
    run.inputs.dataSourceIds.length > 0 ||
    run.inputs.datasetIds.length > 0 ||
    run.inputs.modelEntityIds.length > 0 ||
    run.inputs.pipelineIds.length > 0
  );
  
  const hasOutputs = run.outputs && (
    run.outputs.dataSourceIds.length > 0 ||
    run.outputs.datasetIds.length > 0 ||
    run.outputs.modelEntityIds.length > 0 ||
    run.outputs.pipelineIds.length > 0
  );


  const handleAccept = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsLaunching(true);
    try {
      await triggerLaunchRun({ runId: run.id });
    } catch (error) {
      console.error('Failed to launch run', error);
    } finally {
      setIsLaunching(false);
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
          {/* Run Spec */}
          {run.spec && (
            <div className="px-3 pb-4 space-y-2 border-gray-700/30">
              <div className="text-xs font-mono text-gray-700">
                {run.spec.runName}
              </div>
              <div className="text-xs text-gray-500 leading-relaxed">
                {run.spec.planAndDeliverableDescriptionForUser}
              </div>
              {run.spec.questionsForUser && (
                <div className="mt-2">
                  <div className="text-[10px] font-medium text-gray-600 mb-1">Questions:</div>
                  <div className="text-xs text-gray-500 leading-relaxed">
                    {run.spec.questionsForUser}
                  </div>
                </div>
              )}
              {run.spec.configurationDefaultsDescription && (
                <div className="mt-2 pt-2">
                  <div className="text-[10px] font-medium text-gray-600 mb-1">Default Configuration:</div>
                  <div className="text-xs text-gray-500 leading-relaxed">
                    {run.spec.configurationDefaultsDescription}
                  </div>
                </div>
              )}
              
              {/* Entity Context - Inputs */}
              {hasInputs && (
                <div className="pt-2">
                  <div className="text-[10px] font-medium text-gray-600 mb-1">Inputs:</div>
                  <div className="flex flex-wrap gap-1">
                    {run.inputs?.dataSourceIds.map((dataSourceId) => (
                      <div
                        key={dataSourceId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-gray-200 text-gray-600"
                      >
                        <Database size={12} />
                        {dataSources?.find((ds: DataSource) => ds.id === dataSourceId)?.name || 'Data Source'}
                      </div>
                    ))}
                    {run.inputs?.datasetIds.map((datasetId) => (
                      <div
                        key={datasetId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                      >
                        <Folder size={12} />
                        {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                      </div>
                    ))}
                    {run.inputs?.modelEntityIds.map((modelEntityId) => (
                      <div
                        key={modelEntityId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                      >
                        <Brain size={12} />
                        {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                      </div>
                    ))}
                    {run.inputs?.pipelineIds.map((pipelineId) => (
                      <div
                        key={pipelineId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#840B08]/20 text-[#840B08]"
                      >
                        <Zap size={12} />
                        {pipelines?.find((p: Pipeline) => p.id === pipelineId)?.name || 'Pipeline'}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Entity Context - Outputs */}
              {hasOutputs && (
                <div className="pt-2">
                  <div className="text-[10px] font-medium text-gray-600 mb-1">Outputs:</div>
                  <div className="flex flex-wrap gap-1">
                    {run.outputs?.dataSourceIds.map((dataSourceId) => (
                      <div
                        key={dataSourceId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-gray-200 text-gray-600"
                      >
                        <Database size={12} />
                        {dataSources?.find((ds: DataSource) => ds.id === dataSourceId)?.name || 'Data Source'}
                      </div>
                    ))}
                    {run.outputs?.datasetIds.map((datasetId) => (
                      <div
                        key={datasetId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                      >
                        <Folder size={12} />
                        {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                      </div>
                    ))}
                    {run.outputs?.modelEntityIds.map((modelEntityId) => (
                      <div
                        key={modelEntityId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                      >
                        <Brain size={12} />
                        {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                      </div>
                    ))}
                    {run.outputs?.pipelineIds.map((pipelineId) => (
                      <div
                        key={pipelineId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#840B08]/20 text-[#840B08]"
                      >
                        <Zap size={12} />
                        {pipelines?.find((p: Pipeline) => p.id === pipelineId)?.name || 'Pipeline'}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
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
          )}

          {/* Messages */}
          <RunMessageList runId={runId} />
        </>
      )}
    </div>
  );
}